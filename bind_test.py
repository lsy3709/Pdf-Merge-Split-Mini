import socket
from contextlib import closing


def try_bind(address: str, port: int) -> str:
	with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as test_socket:
		test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
			test_socket.bind((address, port))
			bound_port = test_socket.getsockname()[1]
			return f"OK {address}:{bound_port}"
		except Exception as error:
			return f"ERR {address}:{port} -> {error}"


def main() -> None:
	# 단일 포트 바인딩 테스트
	print(try_bind("127.0.0.1", 8000))
	print(try_bind("127.0.0.1", 8001))
	# 랜덤 포트(0) 바인딩 테스트
	print(try_bind("127.0.0.1", 0))
	# 모든 인터페이스 바인딩도 테스트
	print(try_bind("0.0.0.0", 8000))
	print(try_bind("0.0.0.0", 0))


if __name__ == "__main__":
	main()


