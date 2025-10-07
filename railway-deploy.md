# 🚀 Railway 무료 배포 가이드

## 📋 Railway란?
- **완전 무료**: 월 5달러 크레딧 제공
- **Docker 지원**: 완벽 지원
- **자동 배포**: Git 푸시만 하면 자동 배포
- **가입**: GitHub 계정만 있으면 됨

## 🎯 배포 단계

### 1단계: Railway 가입
1. https://railway.app 접속
2. "Login with GitHub" 클릭
3. GitHub 계정으로 로그인

### 2단계: 프로젝트 준비
```bash
# 현재 프로젝트를 GitHub에 푸시
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/imean-project.git
git push -u origin main
```

### 3단계: Railway에서 배포
1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. GitHub 저장소 선택
4. 자동으로 배포 시작!

### 4단계: 환경 변수 설정
Railway 대시보드에서 각 서비스별로 환경 변수 설정:

**Frontend 서비스:**
```
NEXT_PUBLIC_API_URL=https://your-java-api.railway.app/api
NEXT_PUBLIC_PYTHON_API_URL=https://your-python-api.railway.app
```

**Java API 서비스:**
```
DEV_DB_URL=jdbc:mysql://your-mysql.railway.app:3306/i_mean
DEV_DB_USERNAME=root
DEV_DB_PASSWORD=your_password
JWT_SECRET_KEY=your_jwt_secret_key
```

**Python API 서비스:**
```
DB_URL=mysql+aiomysql://root:password@your-mysql.railway.app:3306/i_mean
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret_key
```

## 🎉 완료!
배포가 완료되면 Railway에서 제공하는 URL로 접근 가능합니다!

- Frontend: `https://your-frontend.railway.app`
- Java API: `https://your-java-api.railway.app`
- Python API: `https://your-python-api.railway.app`
