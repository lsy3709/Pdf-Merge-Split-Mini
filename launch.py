from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


def find_free_port(start: int = 8000, end: int = 8010) -> int | None:
	for port in range(start, end + 1):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			try:
				s.bind(("127.0.0.1", port))
				return port
			except OSError:
				continue
	return None


def wait_for_health(port: int, timeout_sec: int = 30) -> bool:
	deadline = time.time() + timeout_sec
	url = f"http://127.0.0.1:{port}/health"
	while time.time() < deadline:
		try:
			with urlopen(url, timeout=2) as resp:  # nosec - local call
				if resp.status == 200:
					return True
		except Exception:
			time.sleep(1)
	return False


def open_browser(port: int) -> None:
	url = f"http://127.0.0.1:{port}"
	if sys.platform.startswith("win"):
		subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
	else:
		import webbrowser
		webbrowser.open(url)


def main() -> int:
	project_root = Path(__file__).parent
	os.chdir(project_root)

	port = find_free_port()
	if port is None:
		print("[ERROR] No free port in 8000..8010")
		return 1

	# uvicorn 서버 실행
	proc = subprocess.Popen(
		[
			sys.executable,
			"-m",
			"uvicorn",
			"app:app",
			"--host",
			"0.0.0.0",
			"--port",
			str(port),
			"--lifespan",
			"off",
		],
		shell=False,
	)

	# 헬스 체크 성공 시 브라우저 오픈
	if wait_for_health(port, timeout_sec=30):
		open_browser(port)
	else:
		print("[WARN] Server not responding yet; open browser manually.")

	# 서버 프로세스가 종료될 때까지 대기
	proc.wait()
	return proc.returncode or 0


if __name__ == "__main__":
	sys.exit(main())


