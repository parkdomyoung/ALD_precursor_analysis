# Contributing

작은 단위의 재현 가능한 변경을 환영합니다. PR을 열기 전에 아래 항목을 확인하세요.

1. Python 3.11 환경에서 `python -m unittest discover -s tests -v`를 실행합니다.
2. `python scripts/validate_repository.py`가 통과하는지 확인합니다.
3. 노트북은 저장소 루트에서 위에서 아래로 실행하고, 실행 순서가 뒤섞인 output을 커밋하지 않습니다.
4. 대용량 checkpoint, 파생 CSV, 임시 figure는 `artifacts/`에 두고 Git에 추가하지 않습니다.
5. API key나 token은 환경 변수 또는 GitHub Secrets로 전달하며 노트북, URL, 로그, manifest에 넣지 않습니다.
6. 모델 변경에는 데이터 hash, split 방법과 seed, preprocessing schema, 비교 지표를 함께 기록합니다.
7. 데이터나 외부 코드를 추가할 때 출처, 고정 버전, 라이선스와 필요한 인용을 문서화합니다.

전체 학습은 CI에 넣지 않습니다. 대신 작은 fixture를 사용한 전처리·shape·직렬화 smoke test를 추가하고, 전체 실험 결과는 별도 artifact로 보존하세요.

