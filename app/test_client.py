import asyncio
import websockets
import json
import jwt
from datetime import datetime, timedelta

# 테스트용 JWT 토큰 생성
def create_test_token(user_id: str):
    secret_key = "your-secret-key-here"  # config.py의 SECRET_KEY와 동일하게 설정
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

async def test_chat_client(user_id: str, room_id: int):
    # JWT 토큰 생성
    token = create_test_token(user_id)
    
    # 웹소켓 연결
    uri = f"ws://localhost:8000/ws/{room_id}/{token}"
    async with websockets.connect(uri) as websocket:
        print(f"사용자 {user_id}가 채팅방 {room_id}에 연결되었습니다.")
        
        # 메시지 수신 태스크
        async def receive_messages():
            while True:
                try:
                    message = await websocket.recv()
                    print(f"수신: {message}")
                except websockets.exceptions.ConnectionClosed:
                    print("연결이 종료되었습니다.")
                    break
        
        # 메시지 수신 태스크 시작
        receive_task = asyncio.create_task(receive_messages())
        
        # 사용자 입력 처리
        while True:
            try:
                message = input("메시지를 입력하세요 (종료하려면 'quit' 입력): ")
                if message.lower() == 'quit':
                    break
                    
                # 메시지 전송
                await websocket.send(json.dumps({
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except KeyboardInterrupt:
                break
        
        # 수신 태스크 취소
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass

async def main():
    # 테스트할 사용자 수 선택
    print("테스트할 사용자 수를 선택하세요 (1 또는 2):")
    num_users = int(input())
    
    room_id = 1  # 테스트용 채팅방 ID
    
    if num_users == 1:
        # 단일 사용자 테스트
        user_id = "user1"
        await test_chat_client(user_id, room_id)
    else:
        # 두 사용자 동시 테스트
        user1_task = asyncio.create_task(test_chat_client("user1", room_id))
        user2_task = asyncio.create_task(test_chat_client("user2", room_id))
        
        # 두 사용자 중 하나라도 종료되면 모두 종료
        done, pending = await asyncio.wait(
            [user1_task, user2_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 남은 태스크 취소
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main()) 