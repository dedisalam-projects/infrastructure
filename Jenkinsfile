pipeline {
    agent any

    options {
        timeout(time: 15, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    parameters {
        string(
            name: 'SERVICES', 
            defaultValue: 'all', 
            description: 'Layanan yang akan di-update (default: all untuk sinkronisasi menyeluruh, atau tentukan nama layanan spesifik)'
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
                        docker compose -f docker-compose.prod.yml pull --ignore-pull-failures || true
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
                    sleep 5
                    docker compose -f docker-compose.prod.yml ps
                    
                    echo "Memverifikasi Gateway Healthcheck (http://127.0.0.1:3000/health)..."
                    HEALTHY=false
                    for i in $(seq 1 40); do
                        if docker compose -f docker-compose.prod.yml exec -T gateway wget --quiet --tries=1 --spider http://127.0.0.1:3000/health > /dev/null 2>&1; then
                            echo "Gateway sehat dan siap melayani trafik ($i/40)!"
                            HEALTHY=true
                            break
                        fi
                        echo "Menunggu Gateway siap ($i/40)..."
                        sleep 2
                    done

                    if [ "$HEALTHY" != "true" ]; then
                        echo "ERROR: Gateway gagal merespons /health setelah 40 percobaan!"
                        echo "=== Status Kontainer ==="
                        docker compose -f docker-compose.prod.yml ps
                        echo "=== Log Gateway ==="
                        docker compose -f docker-compose.prod.yml logs --tail 50 gateway
                        echo "=== Log User Service ==="
                        docker compose -f docker-compose.prod.yml logs --tail 30 user-service
                        echo "=== Log Notification Service ==="
                        docker compose -f docker-compose.prod.yml logs --tail 30 notification-service
                        exit 1
                    fi
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
            withCredentials([string(credentialsId: 'discord-webhook-url', variable: 'DISCORD_WEBHOOK')]) {
                sh '''
                    curl -s -X POST -H "Content-Type: application/json" \
                        -d "{
                            \\"embeds\\": [{
                                \\"title\\": \\"✅ [SUCCESS] ${JOB_NAME} - #${BUILD_NUMBER}\\",
                                \\"description\\": \\"Deployment infrastruktur produksi berhasil diperbarui!\\\\n**Host:** ThinkCentre (172.16.254.2)\\\\n[Lihat Build di Jenkins](${BUILD_URL})\\\\n[Lihat Dashboard Grafana](http://172.16.254.2:3050)\\",
                                \\"color\\": 5763719,
                                \\"timestamp\\": \\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\\"
                            }]
                        }" "$DISCORD_WEBHOOK" || true
                '''
            }
        }
        failure {
            echo 'Deployment infrastruktur gagal! Periksa status container di atas.'
            withCredentials([string(credentialsId: 'discord-webhook-url', variable: 'DISCORD_WEBHOOK')]) {
                sh '''
                    curl -s -X POST -H "Content-Type: application/json" \
                        -d "{
                            \\"embeds\\": [{
                                \\"title\\": \\"❌ [FAILED] ${JOB_NAME} - #${BUILD_NUMBER}\\",
                                \\"description\\": \\"Deployment infrastruktur produksi gagal!\\\\n**Host:** ThinkCentre (172.16.254.2)\\\\n[Lihat Console Output Jenkins](${BUILD_URL}console)\\",
                                \\"color\\": 15548997,
                                \\"timestamp\\": \\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\\"
                            }]
                        }" "$DISCORD_WEBHOOK" || true
                '''
            }
        }
    }
}