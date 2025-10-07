#!/bin/bash

# I-mean 프로젝트 배포 스크립트
# 사용법: ./deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}

echo "🚀 I-mean 프로젝트 배포 시작..."
echo "환경: $ENVIRONMENT"

# 환경별 설정
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "📋 프로덕션 환경 배포 준비..."
    
    # 환경 변수 파일 확인
    if [ ! -f "env.prod" ]; then
        echo "❌ env.prod 파일이 없습니다. 먼저 환경 변수를 설정해주세요."
        exit 1
    fi
    
    # 환경 변수 로드
    export $(cat env.prod | grep -v '^#' | xargs)
    
    # Docker Compose 프로덕션 설정 사용
    COMPOSE_FILE="docker-compose.prod.yml"
    
    echo "🔧 프로덕션 설정으로 배포 중..."
    
else
    echo "📋 개발 환경 배포 준비..."
    COMPOSE_FILE="docker-compose.yml"
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker compose -f $COMPOSE_FILE down

# 이미지 재빌드
echo "🔨 Docker 이미지 재빌드 중..."
docker compose -f $COMPOSE_FILE build --no-cache

# 서비스 시작
echo "🚀 서비스 시작 중..."
docker compose -f $COMPOSE_FILE up -d

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 30

echo "📊 서비스 상태 확인:"
docker compose -f $COMPOSE_FILE ps

echo "🌐 접근 URL:"
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "  - 프론트엔드: http://$SERVER_IP"
    echo "  - Java API: http://$SERVER_IP/api"
    echo "  - Python API: http://$SERVER_IP/python"
else
    echo "  - 프론트엔드: http://localhost:3000"
    echo "  - Java API: http://localhost:8080/api"
    echo "  - Python API: http://localhost:8000"
fi

echo "✅ 배포 완료!"
echo ""
echo "📝 로그 확인 명령어:"
echo "  docker compose -f $COMPOSE_FILE logs -f [서비스명]"
echo ""
echo "🛑 서비스 중지 명령어:"
echo "  docker compose -f $COMPOSE_FILE down"
