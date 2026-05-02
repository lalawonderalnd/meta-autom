"""WebSocket endpoints for live session streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/sessions/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str) -> None:
    """Live stream of action events as they happen during a session.

    Server sends JSON events on each action, checkpoint, error, completion.
    """
    await websocket.accept()

    # TODO: Implement - subscribe to session events via Redis pub/sub or similar
    # For now, just keep connection open and close when client disconnects
    try:
        while True:
            # Wait for incoming messages (client can send ping/pong or control commands)
            data = await websocket.receive_text()
            # Echo back for now - in production, handle control commands
            await websocket.send_json({"type": "ack", "message": f"Received: {data}"})
    except WebSocketDisconnect:
        # Client disconnected normally
        pass
    except Exception:
        # Log error but don't crash
        pass
    finally:
        await websocket.close()
