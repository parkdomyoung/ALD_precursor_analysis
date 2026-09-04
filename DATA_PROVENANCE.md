# 데이터 출처와 재현성 기록

## `tmQM_y.csv`

저장소의 `tmQM_y.csv`는 [UiO Computational Catalysis Group의 tmQM 저장소](https://github.com/uiocompcat/tmQM)에 공개된 2024 release 파일과 동일합니다.

| 항목 | 값 |
| --- | --- |
| 원본 경로 | `tmQM/tmQM_y.csv` |
| 고정 원본 commit | [`ece824419c9006fe66436daf233822b75533b82f`](https://github.com/uiocompcat/tmQM/commit/ece824419c9006fe66436daf233822b75533b82f) |
| Git blob SHA | `3d5bbfa75f01a8d334d1e630b07f94dc7d36603f` |
| 파일 크기 | 19,925,955 bytes |
| 데이터 행 | 108,541개(헤더 제외) |
| 구분자 | 세미콜론(`;`) |

주요 열은 `CSD_code`, `Electronic_E`, `Dispersion_E`, `Dipole_M`, `Metal_q`, `HL_Gap`, `HOMO_Energy`, `LUMO_Energy`, `Polarizability`, `CSD_years`, `SMILES`입니다. 원본 설명에 따르면 전자 구조 물성은 DFT(TPSSh-D3BJ/def2-SVP), polarizability는 GFN2-xTB 수준에서 계산됐습니다. 이 저장소의 모델은 `HL_Gap`을 Hartree 단위 회귀 target으로 사용합니다.

데이터를 사용한 결과에는 다음 논문과 데이터 저장소를 인용하세요.

- Balcells, D.; Skjelstad, B. B. “The tmQM Dataset—Quantum Geometries and Properties of 86k Transition Metal Complexes.” *J. Chem. Inf. Model.* 2020. [doi:10.1021/acs.jcim.0c01041](https://doi.org/10.1021/acs.jcim.0c01041)
- [tmQM 2024 release repository](https://github.com/uiocompcat/tmQM/tree/ece824419c9006fe66436daf233822b75533b82f)

원본 저장소는 MIT License를 선언합니다. 해당 고지는 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)에 보존했습니다. tmQM 구조가 Cambridge Structural Database에서 유래한 만큼, 재배포나 상업적 사용 전에는 원본 저장소와 CCDC/CSD 조건도 확인해야 합니다.

## `DFT_OUTPUT/`

`1.out`–`10.out`은 ORCA 6.1.0으로 수행한 10개 ALD 전구체의 단일점 계산 출력입니다. 모든 파일은 `TPSSh D3BJ def2-SVP NormalSCF`, charge 0, multiplicity 1 조건을 기록하며 `ORCA TERMINATED NORMALLY`로 끝납니다. 파일별 화합물과 최종 orbital gap은 [`DFT_OUTPUT/README.md`](DFT_OUTPUT/README.md)와 `data/ald_precursors.csv`에 정리했습니다.

현재 남아 있는 provenance 공백은 최초 3D geometry 출처, geometry 생성·최적화 과정, `.inp` 원본입니다. 후속 계산을 추가할 때는 입력 파일, ORCA 버전, 명령, 구조 출처, checksum을 함께 보존하세요.

## OpenAlex 문헌 메타데이터

`scripts/fetch_openalex.py`는 [OpenAlex Works API](https://help.openalex.org/api/)에서 실행 시점에 논문 메타데이터를 수집합니다. 원격 데이터는 계속 갱신되므로 같은 검색식도 실행 날짜에 따라 달라질 수 있습니다.

재현성을 위해 스크립트는 CSV 옆 manifest에 다음을 기록합니다.

- endpoint와 검색식
- 시작·종료 연도
- 요청한 최대 결과 수와 실제 저장 수
- cursor page 수와 API가 보고한 전체 후보 수
- UTC 수집 시각
- API key 사용 여부(키 값은 기록하지 않음)

OpenAlex ID와 DOI도 CSV에 저장해 중복 제거와 원문 추적에 사용합니다. 생성된 CSV와 manifest는 기본적으로 `artifacts/` 아래에 저장되며 Git에 포함하지 않습니다.

## 모델 결과 재현 시 기록할 항목

새 실험 결과를 공유할 때 최소한 아래를 함께 남기세요.

1. Git commit SHA와 Python/package 버전
2. 입력 데이터 blob 또는 SHA-256
3. train/validation/test 분할 ID와 seed
4. 전처리·descriptor schema
5. 모델 hyperparameter와 checkpoint
6. MAE, RMSE, R² 및 평가 집합 정의
7. 생성한 표·그림의 실행 명령

