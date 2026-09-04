# ALD Precursor Analysis

tmQM 전이금속 착물 데이터로 ALD(Atomic Layer Deposition) 전구체 후보의 HOMO–LUMO gap을 예측하고, OpenAlex 문헌 데이터로 ALD 연구 키워드 변화를 살펴보는 탐색형 연구 저장소입니다.

> **연구용 주의사항**  
> 이 저장소의 예측값은 후보 탐색을 위한 계산 결과입니다. HOMO–LUMO gap 하나만으로 실제 ALD 공정 적합성(휘발성, 열 안정성, 표면 반응성, 독성, 공정 윈도우)을 판단할 수 없습니다.

## 구성

| 경로 | 역할 | 주요 입력 | 생성 파일 |
| --- | --- | --- | --- |
| `ALD_LGBM.ipynb` | Morgan fingerprint와 RDKit descriptor 기반 LightGBM 회귀 | `tmQM_y.csv` | `tmQM_cleaned.csv` |
| `ALD_GNN.ipynb` | SMILES를 분자 그래프로 바꿔 GCN 회귀 | `tmQM_y.csv` | `best_gnn_model.pt`, `gnn_training_results.png` |
| `ALD_textmining.ipynb` | OpenAlex 논문 제목의 uni/bi-gram 변화 분석 | OpenAlex Works API | `artifacts/openalex/ald_openalex_data.csv` |
| `scripts/fetch_openalex.py` | 재시도·cursor pagination·manifest를 포함한 문헌 수집 CLI | OpenAlex Works API | CSV와 `.manifest.json` |
| `DFT_OUTPUT/` | 10개 ALD 전구체의 ORCA 단일점 계산 원본 출력 | ORCA 입력 구조 | `1.out`–`10.out` |
| `data/ald_precursors.csv` | 전구체 이름, SMILES, DFT 파일, 기준 gap 매핑 | `DFT_OUTPUT/` | 모델 비교용 공통 입력 |

데이터와 계산 조건은 [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md), DFT 파일별 매핑은 [`DFT_OUTPUT/README.md`](DFT_OUTPUT/README.md)를 참고하세요.

## 빠른 시작

Python 3.11을 기준 환경으로 권장합니다.

```bash
python -m venv .venv
```

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

설치 후 저장소 루트에서 다음을 실행합니다.

```bash
python scripts/validate_repository.py
jupyter lab
```

각 노트북은 서로 독립적입니다. `ALD_LGBM.ipynb`와 `ALD_GNN.ipynb`는 저장소 루트의 `tmQM_y.csv`를 읽으므로 루트에서 Jupyter를 시작해야 합니다. GNN 전체 학습은 GPU를 권장하며 CPU에서는 오래 걸릴 수 있습니다. CUDA 환경은 운영체제와 GPU에 맞는 PyTorch 설치 명령을 먼저 확인하세요.

## OpenAlex 문헌 수집

노트북과 동일한 2015년 이후 자료를 현재 연도까지 수집하는 예시는 다음과 같습니다.

```bash
python scripts/fetch_openalex.py --start-year 2015 --max-results 2000
```

기본 출력은 `artifacts/openalex/ald_openalex_data.csv`이며, 같은 위치에 검색식·기간·수집 시각·레코드 수를 기록한 manifest도 생성됩니다. OpenAlex는 소규모 익명 요청을 허용하지만, 반복 수집에는 API key 사용을 권장합니다. 키는 저장소에 저장하지 말고 실행 환경에만 설정하세요.

PowerShell:

```powershell
$env:OPENALEX_API_KEY = "your-key"
python scripts/fetch_openalex.py --start-year 2015 --max-results 2000
```

macOS/Linux:

```bash
export OPENALEX_API_KEY="your-key"
python scripts/fetch_openalex.py --start-year 2015 --max-results 2000
```

키는 `Authorization: Bearer ...` 헤더로만 전달되며 CSV, manifest, 로그에 기록되지 않습니다.

## 저장된 결과의 해석

현재 노트북 출력에는 다음 탐색 결과가 남아 있습니다.

| 모델 | 학습 범위 | 저장된 결과 |
| --- | --- | --- |
| GNN | 분자량 500 이하 30,795개 그래프 | MAE 0.0139 Hartree, R² 0.7250 |
| LightGBM | 유효 SMILES 100,831개 | R² 0.7532 |

이 수치는 동일한 모집단과 평가 절차로 얻은 정식 benchmark가 아닙니다. 특히 현재 GNN 노트북은 epoch마다 test split으로 scheduler와 checkpoint를 선택하므로 test 정보가 모델 선택에 사용됩니다. 또한 두 노트북의 모집단과 전처리가 다릅니다. 숫자는 기존 실행을 이해하기 위한 기록으로만 사용하고, publication-grade 비교 전에는 validation/test 분리와 scaffold split을 적용해 다시 평가하세요.

## 알려진 한계와 다음 단계

- tmQM은 ALD 전구체 전용 데이터가 아니라 전이금속 착물의 넓은 화학 공간입니다.
- 무작위 분할은 유사한 scaffold가 train/test 양쪽에 들어가 일반화 성능을 낙관적으로 보일 수 있습니다.
- GNN은 현재 생성한 `edge_attr`를 `GCNConv`에 전달하지 않아 결합 종류를 학습에 사용하지 않습니다.
- LightGBM은 전체 데이터에서 결측값 중앙값을 계산한 뒤 분할하며, 신규 전구체에서는 다른 결측값 규칙을 사용합니다.
- RDKit descriptor를 동적으로 탐색하므로 RDKit 버전에 따라 feature schema가 달라질 수 있습니다.
- DFT 구조의 최초 출처와 입력 생성 절차는 아직 기록되지 않았습니다.

다음 모델링 PR에서는 train/validation/test 또는 scaffold split, train-only imputation, 고정 descriptor schema, edge-aware GNN, seed·split·dataset hash 저장을 함께 적용하는 것이 안전합니다.

## 검증

전체 모델 학습이나 외부 API 호출 없이 저장소 구조와 작은 단위 테스트를 실행할 수 있습니다.

```bash
python -m unittest discover -s tests -v
python scripts/validate_repository.py
```

GitHub Actions도 같은 검사를 수행합니다. 전체 ML 학습과 OpenAlex 네트워크 요청은 CI에서 실행하지 않습니다.

## 라이선스

이 저장소 자체의 코드 라이선스는 아직 선언되지 않았습니다. 재사용을 허용하려면 저장소 소유자가 프로젝트 라이선스를 명시적으로 선택해야 합니다. 포함된 tmQM 파일은 제3자 자료이며 원 저작권과 고지는 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)를 따릅니다.

