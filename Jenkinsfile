pipeline {
    agent any

    environment {
        IMAGE_NAME = "ads-ingestion-service"
        DOCKER_REPO = "docker.io/mayerll"
        REGISTRY_CREDENTIAL = "dockerhub-credential"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Set Variables') {
            steps {
                script {
                    COMMIT_ID = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    IMAGE_TAG = "${env.BRANCH_NAME}-${COMMIT_ID}-${env.BUILD_NUMBER}"
                    echo "Docker tag: ${IMAGE_TAG}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest tests/'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                docker build -t ${DOCKER_REPO}/${IMAGE_NAME}:${IMAGE_TAG} .
                """
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                        credentialsId: REGISTRY_CREDENTIAL,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS')]) {

                    sh """
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker push ${DOCKER_REPO}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker logout
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                script {

                    def namespace = ""
                    def credentialId = ""
                    def clusterName = ""

                    if (env.BRANCH_NAME.startsWith('feature/')) {
                        echo "Feature branch - Build only, no deployment"
                        return
                    }
                    else if (env.BRANCH_NAME == 'develop') {
                        namespace = "ads-dev"
                        credentialId = "kubeconfig-dev"
                        clusterName = "DEV"
                    }
                    else if (env.BRANCH_NAME == 'qa') {
                        namespace = "ads-qa"
                        credentialId = "kubeconfig-qa"
                        clusterName = "QA"
                    }
                    else if (env.BRANCH_NAME == 'staging') {
                        namespace = "ads-staging"
                        credentialId = "kubeconfig-staging"
                        clusterName = "STAGING"
                    }
                    else if (env.BRANCH_NAME == 'main') {
                        namespace = "ads-prod"
                        credentialId = "kubeconfig-prod"
                        clusterName = "PRODUCTION"

                        // Production approval gate
                        input message: "Deploy to PRODUCTION?"
                    }
                    else if (env.BRANCH_NAME.startsWith('hotfix/')) {
                        namespace = "ads-prod"
                        credentialId = "kubeconfig-prod"
                        clusterName = "PRODUCTION"
                    }
                    else {
                        echo "Branch ${env.BRANCH_NAME} does not trigger deployment"
                        return
                    }

                    echo "Deploying to ${clusterName} cluster"
                    echo "Namespace: ${namespace}"

                    withCredentials([file(credentialsId: credentialId, variable: 'KUBECONFIG_FILE')]) {

                        try {

                            sh """
                            export KUBECONFIG=$KUBECONFIG_FILE

                            # Ensure namespace exists
                            kubectl get ns ${namespace} || kubectl create ns ${namespace}

                            # Update image
                            kubectl set image deployment/${IMAGE_NAME} \
                            ${IMAGE_NAME}=${DOCKER_REPO}/${IMAGE_NAME}:${IMAGE_TAG} \
                            -n ${namespace}

                            # Wait for rollout
                            kubectl rollout status deployment/${IMAGE_NAME} \
                            -n ${namespace} --timeout=180s
                            """

                            echo "Deployment successful 🚀"

                        } catch (err) {

                            echo "Deployment failed! Rolling back..."

                            sh """
                            export KUBECONFIG=$KUBECONFIG_FILE
                            kubectl rollout undo deployment/${IMAGE_NAME} -n ${namespace}
                            """

                            error("Deployment failed and rolled back.")
                        }
                    }
                }
            }
        }
    }

    post {

        success {
            echo "Pipeline SUCCESS ✅"
        }

        failure {
            echo "Pipeline FAILED ❌"
        }

        always {
            cleanWs()
        }
    }
}
