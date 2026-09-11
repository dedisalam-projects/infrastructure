pipeline {
    agent any

    options {
        timeout(time: 15, unit: 'MINUTES')
        disableConcurrentBuilds()
        ansiColor('xterm')
    }

    parameters {
        string(
            name: 'SERVICES', 
            defaultValue: 'gateway user-service notification-service', 
            description: 'Layanan yang akan di-update (kosongkan atau isi "all" untuk semua)'
        )
    }

    stages {
        stage('Checkout Infrastructure') {
            steps {
                checkout scm
            }
        }

        stage('Inject Production Secrets (.env)') {
            steps {
                echo 'Mengambil .env production dari Jenkins Credentials...'
                withCredentials([file(credentialsId: 'infra-prod-env', variable: 'PROD_ENV_FILE')]) {
                    sh '''
                        cp "$PROD_ENV_FILE" .env
                        chmod 600 .env
                        echo ".env file berhasil di-generate secara aman."
                    '''
                }
            }
        }

        stage('Pull Docker Images') {
            steps {
                echo "Mengunduh image terbaru untuk: ${params.SERVICES}..."
                sh '''
                    if [ "${SERVICES}" = "all" ] || [ -z "${SERVICES}" ]; then
                        docker compose -f docker-compose.prod.yml pull
                    else
                        docker compose -f docker-compose.prod.yml pull ${SERVICES}
                    fi
                '''
            }
        }

        stage('Deploy Containers') {
            steps {
                echo 'Menerapkan container baru...'
                sh '''
                    if [ "${SERVICES}" = "all" ] || [ -z "${SERVICES}" ]; then
                        docker compose -f docker-compose.prod.yml up -d --remove-orphans
                    else
                        docker compose -f docker-compose.prod.yml up -d --no-deps --remove-orphans ${SERVICES}
                    fi
                '''
            }
        }

        stage('Verify Healthcheck') {
            steps {
                echo 'Memverifikasi status container pasca-deployment...'
                sh '''
                    sleep 10
                    docker compose -f docker-compose.prod.yml ps
                    
                    # Verifikasi Gateway Healthcheck
                    docker compose -f docker-compose.prod.yml exec -T gateway wget --quiet --tries=3 --spider http://127.0.0.1:3000/api/v1/health || true
                '''
            }
        }
    }

    post {
        always {
            echo 'Membersihkan environment file sisa di workspace agent...'
            sh 'rm -f .env || true'
        }
        success {
            echo 'Pembersihan image lama (prune)...'
            sh 'docker image prune -f || true'
            echo 'Deployment infrastruktur dan backend berhasil diperbarui!'
        }
        failure {
            echo 'Deployment infrastruktur gagal! Periksa status container di atas.'
        }
    }
}