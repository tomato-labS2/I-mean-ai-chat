@echo off
REM 가상환경 비활성화는 수동으로 해야 함 (bat 파일 내에서는 불가능)

REM 2. 기존 가상환경 삭제
echo 기존 가상환경 삭제 중...
IF EXIST venv (
    rmdir /s /q venv
    echo 기존 venv 폴더 삭제 완료
) ELSE (
    echo 삭제할 venv 폴더가 없습니다
)

REM 3. 새로운 가상환경 생성
echo 가상환경 생성 중...
python -m venv venv

REM 4. 가상환경 활성화
echo 가상환경 활성화 중...
call venv\Scripts\activate

REM 5. pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip

REM 6. 패키지 설치
echo 패키지 설치 중...
pip install -r app\requirements.txt

echo 모든 작업이 완료되었습니다.
pause
