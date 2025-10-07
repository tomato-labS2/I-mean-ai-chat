# Java Spring Boot 서버 Dockerfile
FROM openjdk:17-jdk-slim

# 작업 디렉토리 설정
WORKDIR /app

# Gradle Wrapper 파일 복사
COPY gradlew .
COPY gradle gradle

# Gradle Wrapper 실행 권한 부여
RUN chmod +x gradlew

# Gradle 의존성 파일 복사
COPY build.gradle .
COPY settings.gradle .

# 소스 코드 복사
COPY src src

# Gradle 의존성 다운로드 및 빌드
RUN ./gradlew build -x test

# 빌드된 JAR 파일 실행
CMD ["java", "-jar", "build/libs/tomatolab_imean-0.0.1-SNAPSHOT.jar"]
