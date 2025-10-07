# 🆓 무료 클라우드 배포 완벽 가이드

## 🎯 추천 순서 (쉬운 순서대로)

### 1순위: Railway (가장 쉬움!) ⭐⭐⭐⭐⭐
- **무료**: 월 5달러 크레딧
- **가입**: GitHub 계정만 있으면 됨
- **배포**: Git 푸시만 하면 자동 배포
- **Docker**: 완벽 지원

### 2순위: Render ⭐⭐⭐⭐
- **무료**: 제한된 리소스
- **가입**: GitHub 계정만 있으면 됨
- **배포**: Git 푸시만 하면 자동 배포

### 3순위: Fly.io ⭐⭐⭐
- **무료**: 제한된 앱 수
- **가입**: 신용카드 필요 (과금 안됨)
- **Docker**: 완벽 지원

## 🚀 Railway 배포 (추천!)

### 단계별 가이드

#### 1단계: GitHub 저장소 생성
```bash
# 현재 프로젝트를 GitHub에 업로드
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/imean-project.git
git push -u origin main
```

#### 2단계: Railway 가입 및 연결
1. https://railway.app 접속
2. "Login with GitHub" 클릭
3. GitHub 계정으로 로그인
4. "New Project" 클릭
5. "Deploy from GitHub repo" 선택
6. GitHub 저장소 선택

#### 3단계: 서비스별 배포
Railway에서는 각 서비스를 별도로 배포해야 합니다:

**A. Frontend 배포:**
1. Railway에서 "New Service" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택
4. Root Directory: `I-mean-frontend-main`
5. 환경 변수 설정:
   ```
   NEXT_PUBLIC_API_URL=https://your-java-api.railway.app/api
   NEXT_PUBLIC_PYTHON_API_URL=https://your-python-api.railway.app
   ```

**B. Java API 배포:**
1. Railway에서 "New Service" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택
4. Root Directory: `I-mean-backend-main`
5. 환경 변수 설정:
   ```
   DEV_DB_URL=jdbc:mysql://your-mysql.railway.app:3306/i_mean
   DEV_DB_USERNAME=root
   DEV_DB_PASSWORD=your_password
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

**C. Python API 배포:**
1. Railway에서 "New Service" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택
4. Root Directory: `I-mean-ai-chat-newdev`
5. 환경 변수 설정:
   ```
   DB_URL=mysql+aiomysql://root:password@your-mysql.railway.app:3306/i_mean
   OPENAI_API_KEY=your_openai_api_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

**D. MySQL 데이터베이스:**
1. Railway에서 "New Service" 클릭
2. "Database" 선택
3. "MySQL" 선택
4. 자동으로 데이터베이스 생성됨

## 🎉 배포 완료!

배포가 완료되면 Railway에서 제공하는 URL로 접근 가능합니다:

- **Frontend**: `https://your-frontend.railway.app`
- **Java API**: `https://your-java-api.railway.app`
- **Python API**: `https://your-python-api.railway.app`
- **MySQL**: Railway 내부에서 자동 연결

## 🔧 문제 해결

### 1. 빌드 실패 시
```bash
# 로컬에서 테스트
docker build -t test-frontend ./I-mean-frontend-main
docker run -p 3000:3000 test-frontend
```

### 2. 환경 변수 설정
Railway 대시보드에서 각 서비스의 "Variables" 탭에서 설정

### 3. 로그 확인
Railway 대시보드에서 각 서비스의 "Logs" 탭에서 실시간 로그 확인

## 💡 추가 팁

### 1. 도메인 연결 (선택사항)
Railway에서 커스텀 도메인 설정 가능

### 2. SSL 인증서
Railway에서 자동으로 HTTPS 인증서 제공

### 3. 모니터링
Railway 대시보드에서 실시간 모니터링 가능

## 🆘 도움이 필요하면

1. Railway 문서: https://docs.railway.app
2. GitHub Issues: 프로젝트 저장소에서 이슈 생성
3. 커뮤니티: Railway Discord 서버 참여
