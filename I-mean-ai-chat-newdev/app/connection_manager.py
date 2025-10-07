from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional, Any, List, Set
import asyncio

class ConnectionManager:
    def __init__(self):
        # 활성 웹소켓 연결 저장: room_id -> user_id -> WebSocket
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        # 방별 메시지 큐: room_id -> asyncio.Queue
        self.pending_messages: Dict[int, asyncio.Queue[Dict[str, Any]]] = {}
        # 방별 메시지 처리 태스크 관리: room_id -> asyncio.Task
        self._message_processor_tasks: Dict[int, asyncio.Task[None]] = {}
        # 특정 방에서 연결이 진행 중(connect 호출 중)임을 나타내는 플래그: room_id -> asyncio.Lock
        self._room_connection_locks: Dict[int, asyncio.Lock] = {}

    async def _get_room_lock(self, room_id: int) -> asyncio.Lock:
        if room_id not in self._room_connection_locks:
            self._room_connection_locks[room_id] = asyncio.Lock()
        return self._room_connection_locks[room_id]

    async def connect(self, websocket: WebSocket, room_id: int, user_id: str):
        log_prefix = f"[CM_CONNECT] Room {room_id} User {user_id} -"
        print(f"{log_prefix} Attempting to connect.")
        
        room_lock = await self._get_room_lock(room_id)
        async with room_lock: # 방 초기화 및 태스크 시작 로직 동기화
            await websocket.accept()
            print(f"{log_prefix} WebSocket accepted.")

            if room_id not in self.active_connections:
                self.active_connections[room_id] = {}
                self.pending_messages[room_id] = asyncio.Queue(maxsize=100)
                print(f"{log_prefix} New room initialized (active_connections, pending_messages with maxsize=100).")
            
            if user_id in self.active_connections[room_id]:
                print(f"{log_prefix} User already connected. Storing new websocket, previous will be orphaned.")
                # 기존 연결이 있다면 명시적으로 닫아주는 것이 좋을 수 있습니다.
                # try:
                #     await self.active_connections[room_id][user_id].close()
                # except Exception as e_close:
                #     print(f"{log_prefix} Error closing previous connection for user {user_id}: {e_close}")
            
            self.active_connections[room_id][user_id] = websocket
            print(f"{log_prefix} Connection established and stored. Current users in room: {list(self.active_connections[room_id].keys())}")

            # 해당 방의 메시지 처리 태스크가 없거나 완료/취소된 경우 새로 시작
            current_task = self._message_processor_tasks.get(room_id)
            if current_task is None or current_task.done():
                if current_task and current_task.done() and not current_task.cancelled():
                    try:
                        await current_task # 이전 태스크의 예외가 있었다면 여기서 발생시켜 로깅
                    except Exception as e_task:
                        print(f"{log_prefix} Previous message processor task for room {room_id} ended with error: {e_task}")
                
                print(f"{log_prefix} Starting new message processor task for room {room_id}.")
                new_task = asyncio.create_task(self.process_messages(room_id))
                self._message_processor_tasks[room_id] = new_task
                # 태스크 완료 시 _message_processor_tasks에서 자동으로 제거 (메모리 누수 방지 목적)
                # 단, 태스크가 정상 종료/취소 외의 예외로 종료될 경우를 고려해야 함.
                new_task.add_done_callback(
                    lambda t, rid=room_id: self._handle_processor_task_completion(t, rid)
                )
            else:
                print(f"{log_prefix} Message processor task for room {room_id} is already running.")

    def _handle_processor_task_completion(self, task: asyncio.Task, room_id: int):
        log_prefix = f"[CM_TASK_COMPLETE] Room {room_id} -"
        try:
            # 태스크 결과를 확인하여 예외가 있었다면 로깅 (이미 connect에서 할 수도 있음)
            if task.cancelled():
                print(f"{log_prefix} Message processor task was cancelled.")
            elif task.exception() is not None:
                print(f"{log_prefix} Message processor task finished with exception: {task.exception()}")
            else:
                print(f"{log_prefix} Message processor task finished successfully.")
        finally:
            # 완료된 태스크가 현재 딕셔너리에 있는 태스크와 동일한 경우에만 제거
            if self._message_processor_tasks.get(room_id) is task:
                del self._message_processor_tasks[room_id]
                print(f"{log_prefix} Removed task from _message_processor_tasks.")

    async def disconnect(self, room_id: int, user_id: str):
        log_prefix = f"[CM_DISCONNECT] Room {room_id} User {user_id} -"
        
        room_lock = await self._get_room_lock(room_id) # 리소스 정리 시에도 락 사용
        async with room_lock:
            if room_id in self.active_connections and user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]
                print(f"{log_prefix} User connection removed from active_connections.")

                if not self.active_connections[room_id]: # 해당 방에 더 이상 사용자가 없으면
                    print(f"{log_prefix} No users left in room. Cleaning up room resources.")
                    del self.active_connections[room_id] # 방 자체를 제거
                    
                    # 메시지 처리 태스크 취소
                    task = self._message_processor_tasks.pop(room_id, None) # pop으로 가져오고 삭제
                    if task and not task.done():
                        print(f"{log_prefix} Cancelling message processor task.")
                        task.cancel()
                        # task.add_done_callback에서 제거되므로 여기서 명시적 del은 필요 없음 (pop 했으므로)
                    
                    # 메시지 큐 정리
                    if room_id in self.pending_messages:
                        queue = self.pending_messages.pop(room_id) # pop으로 가져오고 삭제
                        # 큐에 남은 메시지를 비우는 로직 (필요시)
                        # while not queue.empty():
                        # try:
                        # queue.get_nowait()
                        # queue.task_done()
                        # except asyncio.QueueEmpty:
                        # break
                        print(f"{log_prefix} Pending messages queue removed.")
                    
                    if room_id in self._room_connection_locks: # 락 객체도 정리
                        del self._room_connection_locks[room_id]

                    print(f"{log_prefix} Room resources cleared.")
                else:
                    print(f"{log_prefix} {len(self.active_connections[room_id])} user(s) still in room.")
            else:
                print(f"{log_prefix} User or room not found in active_connections. No action taken.")

    def get_active_connections_for_room(self, room_id: int) -> Dict[str, WebSocket]:
        return self.active_connections.get(room_id, {})

    async def broadcast_to_room(self, room_id: int, message: Dict[str, Any], target_user_id: Optional[str] = None):
        log_prefix = f"[CM_BROADCAST] Room {room_id} -"
        
        # 방이 존재하지 않으면 큐를 초기화
        if room_id not in self.pending_messages:
            print(f"{log_prefix} Initializing pending messages queue for room.")
            self.pending_messages[room_id] = asyncio.Queue(maxsize=100)
            
            # 메시지 프로세서 태스크도 시작
            if room_id not in self._message_processor_tasks or self._message_processor_tasks[room_id].done():
                print(f"{log_prefix} Starting new message processor task.")
                new_task = asyncio.create_task(self.process_messages(room_id))
                self._message_processor_tasks[room_id] = new_task
                new_task.add_done_callback(
                    lambda t, rid=room_id: self._handle_processor_task_completion(t, rid)
                )
        
        print(f"{log_prefix} Queuing message. Type: {message.get('type')}, Target: {target_user_id or 'all'}")
        await self.pending_messages[room_id].put({"message_data": message, "target_user_id": target_user_id})

    async def _send_to_websocket(self, websocket: WebSocket, user_id: str, message_data: Dict[str, Any], room_id: int) -> bool:
        log_prefix = f"[CM_SEND] Room {room_id} User {user_id} -"
        try:
            await websocket.send_json(message_data)
            print(f"{log_prefix} Successfully sent message. Type: {message_data.get('type')}")
            return True
        except WebSocketDisconnect: 
            # WebSocketDisconnect는 주로 receive()에서 발생. send 중에는 다른 예외가 발생할 가능성이 높음.
            # (e.g., RuntimeError if already closed, or websockets.exceptions.ConnectionClosed)
            print(f"{log_prefix} WebSocket was already disconnected. Message type: {message_data.get('type')}.")
            # 이 경우 해당 사용자는 disconnect 로직에서 곧 정리될 것임.
        except RuntimeError as e: # e.g., "Cannot call send_json() on a closed WebSocket"
             print(f"{log_prefix} RuntimeError while sending (likely closed). Message type: {message_data.get('type')}: {e}")
        except Exception as e:
            print(f"{log_prefix} ERROR sending message. Type: {message_data.get('type')}: {str(e)}")
        return False

    async def process_messages(self, room_id: int):
        log_prefix = f"[CM_PROCESS_MSG] Room {room_id} -"
        print(f"{log_prefix} Starting message processing task.")

        try:
            while True: # 루프는 태스크가 cancel 되거나 방이 완전히 정리될 때까지 계속
                if room_id not in self.pending_messages:
                    print(f"{log_prefix} Stopping: pending_messages queue for room is gone.")
                    break

                queued_item: Optional[Dict[str, Any]] = None
                try:
                    # 큐에서 아이템 가져오기 (큐가 비어있으면 대기)
                    queued_item = await self.pending_messages[room_id].get()
                    message_data = queued_item["message_data"]
                    target_user_id = queued_item.get("target_user_id")
                    msg_type = message_data.get('type', 'unknown')

                    print(f"{log_prefix} Dequeued message. Type: {msg_type}, Target: {target_user_id or 'all'}")

                    # 전송 시점에 방과 사용자 연결 상태 재확인
                    room_connections = self.active_connections.get(room_id)
                    print(f"{log_prefix} Active connections in room: {list(room_connections.keys()) if room_connections else 'None'}")
                    
                    if not room_connections: # 해당 방에 현재 아무도 연결되어 있지 않음
                        print(f"{log_prefix} Room inactive (no connections). Discarding message type: {msg_type}")
                        self.pending_messages[room_id].task_done()
                        continue

                    # 전송 대상 웹소켓 목록 필터링
                    sockets_to_send: List[tuple[WebSocket, str]] = [] # (websocket, user_id)
                    if target_user_id:
                        if target_user_id in room_connections:
                            sockets_to_send.append((room_connections[target_user_id], target_user_id))
                            print(f"{log_prefix} Adding target user {target_user_id} to send list")
                        else:
                            print(f"{log_prefix} Target user {target_user_id} not found in active connections. Message type {msg_type} not sent to this user.")
                    else: # 전체 방송
                        sockets_to_send = [(ws, uid) for uid, ws in room_connections.items()]
                        print(f"{log_prefix} Broadcasting to all users: {[uid for _, uid in sockets_to_send]}")
                    
                    if not sockets_to_send:
                        print(f"{log_prefix} No specific users to send message to. Type: {msg_type}")
                        self.pending_messages[room_id].task_done()
                        continue
                    
                    # 메시지 병렬 전송
                    print(f"{log_prefix} Attempting to send message to {len(sockets_to_send)} users")
                    send_results = await asyncio.gather(
                        *[self._send_to_websocket(ws, uid, message_data, room_id) for ws, uid in sockets_to_send],
                        return_exceptions=True # 개별 전송의 예외를 gather가 잡도록 함
                    )

                    for i, result in enumerate(send_results):
                        sent_to_uid = sockets_to_send[i][1]
                        if isinstance(result, Exception): # _send_to_websocket에서 예외 발생 시 (거의 없을 것으로 예상)
                            print(f"{log_prefix} gather captured exception for user {sent_to_uid} while sending type {msg_type}: {result}")
                        elif result is False: # _send_to_websocket에서 False 반환 (전송 실패 로깅 후)
                            print(f"{log_prefix} Failed to send message type {msg_type} to user {sent_to_uid} (as reported by _send_to_websocket).")
                        else:
                            print(f"{log_prefix} Successfully sent message type {msg_type} to user {sent_to_uid}")
                    
                except asyncio.CancelledError:
                    print(f"{log_prefix} Task cancelled during message retrieval or processing.")
                    raise # CancelledError는 다시 raise하여 태스크가 정상적으로 취소 상태가 되도록 함
                except Exception as e_inner_loop:
                    # 예: 큐에서 아이템을 가져오는 중 발생할 수 있는 예상치 못한 오류
                    print(f"{log_prefix} Error in inner message processing loop: {e_inner_loop}. Message: {queued_item}")
                finally:
                    if queued_item and room_id in self.pending_messages:
                        try:
                            self.pending_messages[room_id].task_done()
                        except ValueError: # task_done()이 너무 많이 호출된 경우 (큐가 비었거나 등)
                             print(f"{log_prefix} Warning: ValueError on task_done(). Might be already done or queue mismanaged.")
                        except Exception as e_task_done:
                             print(f"{log_prefix} Warning: Unexpected error on task_done(): {e_task_done}")
        
        except asyncio.CancelledError:
            print(f"{log_prefix} Message processing task was cancelled externally.")
        except Exception as e_outer_loop:
            # 이 루프 자체의 심각한 오류 (거의 발생해서는 안 됨)
            print(f"{log_prefix} CRITICAL: Unhandled error in outer processing loop: {e_outer_loop}")
        finally:
            print(f"{log_prefix} Message processing task finished.")
            # _handle_processor_task_completion 콜백에서 최종 정리 (딕셔너리에서 태스크 제거 등) 