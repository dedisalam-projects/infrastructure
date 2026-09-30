pipeline {
    agent any

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
        PROD_COMPOSE_FILE = 'docker-compose.prod.yml'
        SERVICES = "${params.SERVICES ?: 'all'}"
    }

    parameters {
        string(name: 'SERVICES', defaultValue: 'all', description: 'Space-separated list of services to update, or "all" for full stack update.')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Deploying branch: ${env.BRANCH_NAME}"
            }
        }

        stage('Prepare Secrets') {
            steps {
                echo 'Injecting production secrets securely...'
                withCredentials([file(credentialsId: 'infra-prod-env', variable: 'PROD_ENV_FILE')]) {
                    sh 'cp $PROD_ENV_FILE .env'
                    sh 'chmod 600 .env'
                }
            }
        }

        stage('Deploy Production Stack') {
            steps {
                script {
                    if (SERVICES == 'all') {
                        echo "Menjalankan deployment penuh untuk seluruh stack produksi..."
                        sh "docker compose -f ${COMPOSE_FILE} -f ${PROD_COMPOSE_FILE} --profile monitoring up -d --build"
                    } else {
                        echo "Update parsial: Mendownload dan merestart layanan tertentu saja (${SERVICES})..."
                        sh "docker compose -f ${COMPOSE_FILE} -f ${PROD_COMPOSE_FILE} --profile monitoring pull ${SERVICES}"
                        sh "docker compose -f ${COMPOSE_FILE} -f ${PROD_COMPOSE_FILE} --profile monitoring up -d --no-deps ${SERVICES}"
                    }
                }
            }
        }

        stage('Verify Health') {
            steps {
                echo 'Menunggu layanan stabil (15 detik)...'
                sleep 15
                
                echo 'Memeriksa status container:'
                sh 'docker compose -f ${COMPOSE_FILE} -f ${PROD_COMPOSE_FILE} --profile monitoring ps'

                echo 'Memastikan Gateway merespon:'
                sh 'curl -f http://localhost:4000/health || echo "Peringatan: Gateway health check gagal atau endpoint tidak tersedia"'
            }
        }
    }

    post {
        always {
            echo 'Membersihkan secrets dari workspace (Security Post-deployment)'
            sh 'rm -f .env'
        }
        success {
            echo 'Pembersihan image lama (prune)...'
            sh 'docker image prune -f || true'
            echo 'Deployment infrastruktur dan backend berhasil diperbarui!'
            withCredentials([
                string(credentialsId: 'telegram-bot-token', variable: 'TELEGRAM_BOT_TOKEN')
            ]) {
                sh '''
                    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                        -d "chat_id=-1004361815779" \
                        -d "message_thread_id=8" \
                        -d "parse_mode=Markdown" \
                        -d "text=✅ *[SUCCESS]* ${JOB_NAME} - #${BUILD_NUMBER}%0ADeployment infrastruktur produksi berhasil diperbarui!%0A**Host:** ThinkCentre (172.16.254.2)%0A[Lihat Build di Jenkins](${BUILD_URL})%0A[Lihat Dashboard Grafana](http://172.16.254.2:3050)" || true
                '''
            }
        }
        failure {
            echo 'Deployment infrastruktur gagal! Periksa status container di atas.'
            withCredentials([
                string(credentialsId: 'telegram-bot-token', variable: 'TELEGRAM_BOT_TOKEN')
            ]) {
                sh '''
                    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                        -d "chat_id=-1004361815779" \
                        -d "message_thread_id=8" \
                        -d "parse_mode=Markdown" \
                        -d "text=❌ *[FAILED]* ${JOB_NAME} - #${BUILD_NUMBER}%0ADeployment infrastruktur produksi gagal!%0A**Host:** ThinkCentre (172.16.254.2)%0A[Lihat Console Output Jenkins](${BUILD_URL}console)" || true
                '''
            }
        }
    }
}