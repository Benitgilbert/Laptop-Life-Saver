import os
import pytest
from agent.local_buffer import CircularBuffer

@pytest.fixture
def temp_buffer(tmp_path):
    # Create a buffer using a temporary file
    buf_file = tmp_path / "test_buffer.json"
    return CircularBuffer(maxlen=5, filepath=str(buf_file))

def test_buffer_append(temp_buffer):
    temp_buffer.append({"id": 1})
    temp_buffer.append({"id": 2})
    assert len(temp_buffer) == 2

def test_buffer_overflow(temp_buffer):
    # Max size is 5
    for i in range(10):
        temp_buffer.append({"id": i})
    assert len(temp_buffer) == 5
    # Should keep the newest 5 (5,6,7,8,9)
    assert temp_buffer.peek()[0]["id"] == 5

def test_buffer_persistence(tmp_path):
    buf_file = tmp_path / "persist_buffer.json"
    buf1 = CircularBuffer(maxlen=10, filepath=str(buf_file))
    buf1.append({"data": "hello"})
    
    # New instance loading from same file
    buf2 = CircularBuffer(maxlen=10, filepath=str(buf_file))
    assert len(buf2) == 1
    assert buf2.peek()[0]["data"] == "hello"

def test_buffer_remove_first(temp_buffer):
    for i in range(5):
        temp_buffer.append({"id": i})
    temp_buffer.remove_first(2)
    assert len(temp_buffer) == 3
    assert temp_buffer.peek()[0]["id"] == 2
