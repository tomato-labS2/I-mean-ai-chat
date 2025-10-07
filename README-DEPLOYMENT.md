# 🚀 I-mean 프로젝트 배포 가이드

## 📋 배포 옵션

### 1. 로컬 개발 환경 (현재 상태)
```bash
# 현재 실행 중인 서비스들
- Frontend: http://localhost:3000
- Java API: http://localhost:8080
- Python API: http://localhost:8000
- MySQL: localhost:9915
```

### 2. 클라우드 서버 배포

#### **A. AWS EC2 배포 (추천)**

1. **EC2 인스턴스 생성**
   - Ubuntu 20.04 LTS
   - t3.medium 이상 (2GB RAM, 2 vCPU)
   - 보안 그룹: HTTP(80), HTTPS(443), SSH(22), Custom(3000, 8000, 8080)

2. **서버 설정**
   ```bash
   # Docker 설치
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo usermod -aG docker ubuntu
   
   # Docker Compose 설치
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **프로젝트 배포**
   ```bash
   # 프로젝트 클론
   git clone <your-repo-url>
   cd Imean원본
   
   # 환경 변수 설정
   cp env.prod .env
   # .env 파일을 편집하여 실제 값들로 변경
   
   # 배포 실행
   ./deploy.sh prod
   ```

#### **B. Google Cloud Platform (GCP)**

1. **Compute Engine 인스턴스 생성**
   - Ubuntu 20.04 LTS
   - e2-standard-2 이상
   - 방화벽 규칙 설정

2. **배포 과정은 AWS와 동일**

#### **C. Azure 배포**

1. **Virtual Machine 생성**
   - Ubuntu 20.04 LTS
   - Standard_B2s 이상
   - 네트워크 보안 그룹 설정

2. **배포 과정은 AWS와 동일**

### 3. 컨테이너 오케스트레이션 배포

#### **A. Kubernetes (GKE, EKS, AKS)**

1. **Docker 이미지 빌드 및 푸시**
   ```bash
   # Docker Hub에 이미지 푸시
   docker build -t your-username/imean-frontend ./I-mean-frontend-main
   docker build -t your-username/imean-java-api ./I-mean-backend-main
   docker build -t your-username/imean-python-api ./I-mean-ai-chat-newdev
   
   docker push your-username/imean-frontend
   docker push your-username/imean-java-api
   docker push your-username/imean-python-api
   ```

2. **Kubernetes 매니페스트 생성**
   ```yaml
   # k8s-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: imean-frontend
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: imean-frontend
     template:
       metadata:
         labels:
           app: imean-frontend
       spec:
         containers:
         - name: frontend
           image: your-username/imean-frontend:latest
           ports:
           - containerPort: 3000
   ```

#### **B. Docker Swarm**

```bash
# Swarm 초기화
docker swarm init

# 스택 배포
docker stack deploy -c docker-compose.prod.yml imean-stack
```

## 🔧 환경 변수 설정

### 프로덕션 환경 변수 (env.prod)

```bash
# 데이터베이스 설정
MYSQL_ROOT_PASSWORD=your_secure_root_password_here
MYSQL_USER=imean_user
MYSQL_PASSWORD=your_secure_db_password_here

# JWT 보안 키 (최소 32자 이상의 랜덤 문자열)
JWT_SECRET_KEY=your_very_long_and_secure_jwt_secret_key_here_make_it_at_least_32_characters_long

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here

# 이메일 설정
MAIL_USERNAME=your_email@domain.com
MAIL_PASSWORD=your_email_password_here

# 서버 IP 주소
SERVER_IP=your_server_ip_here
```

## 🚀 배포 명령어

### 개발 환경
```bash
./deploy.sh dev
```

### 프로덕션 환경
```bash
./deploy.sh prod
```

## 📊 모니터링 및 관리

### 서비스 상태 확인
```bash
docker compose -f docker-compose.prod.yml ps
```

### 로그 확인
```bash
# 전체 로그
docker compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f java-api
docker compose -f docker-compose.prod.yml logs -f python-api
```

### 서비스 재시작
```bash
docker compose -f docker-compose.prod.yml restart [서비스명]
```

### 서비스 중지
```bash
docker compose -f docker-compose.prod.yml down
```

## 🔒 보안 설정

### 1. 방화벽 설정
```bash
# UFW 방화벽 설정
sudo ufw allow 22    # SSH
sudo ufw allow 80   # HTTP
sudo ufw allow 443  # HTTPS
sudo ufw enable
```

### 2. SSL 인증서 설정
```bash
# Let's Encrypt 인증서 발급
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

### 3. 데이터베이스 백업
```bash
# MySQL 백업
docker exec imean-mysql-prod mysqldump -u root -p i_mean > backup.sql

# 복원
docker exec -i imean-mysql-prod mysql -u root -p i_mean < backup.sql
```

## 📈 성능 최적화

### 1. 리소스 제한 설정
```yaml
# docker-compose.prod.yml에 추가
services:
  java-api:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### 2. 로드 밸런싱
```yaml
# nginx.conf에 로드 밸런싱 설정
upstream java-api {
    server java-api-1:8080;
    server java-api-2:8080;
}
```

## 🆘 문제 해결

### 1. 포트 충돌
```bash
# 포트 사용 중인 프로세스 확인
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :8080
```

### 2. 메모리 부족
```bash
# 메모리 사용량 확인
free -h
docker stats
```

### 3. 디스크 공간 부족
```bash
# 디스크 사용량 확인
df -h
docker system prune -f
```

## 📞 지원

배포 과정에서 문제가 발생하면:
1. 로그 확인: `docker compose logs -f`
2. 서비스 상태 확인: `docker compose ps`
3. 리소스 사용량 확인: `docker stats`
