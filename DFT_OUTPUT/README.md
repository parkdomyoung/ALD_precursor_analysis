# DFT reference outputs

이 디렉터리에는 10개 ALD 전구체의 ORCA 6.1.0 단일점 계산 출력이 있습니다.

공통 계산 설정:

- method: `TPSSh D3BJ def2-SVP NormalSCF`
- charge: `0`
- multiplicity: `1`
- parallel processes: `8`
- `%maxcore`: `3500 MB`
- status: 10개 파일 모두 `ORCA TERMINATED NORMALLY`

| 파일 | 전구체 | HOMO–LUMO gap (Hartree) |
| --- | --- | ---: |
| `1.out` | TDMAH | 0.184442 |
| `2.out` | TEMAH | 0.144798 |
| `3.out` | TDEAH | 0.172795 |
| `4.out` | TDMAT | 0.151902 |
| `5.out` | HfCl4 | 0.256719 |
| `6.out` | TiCl4 | 0.181093 |
| `7.out` | TTIP | 0.196301 |
| `8.out` | TDMAZ | 0.154910 |
| `9.out` | TMA | 0.223108 |
| `10.out` | ZrCl4 | 0.237103 |

gap은 각 파일의 마지막 `ORBITAL ENERGIES` 표에서 LUMO energy와 HOMO energy의 차이로 확인했습니다. 모델 입력에 쓰는 SMILES와 파일 경로를 함께 읽으려면 [`../data/ald_precursors.csv`](../data/ald_precursors.csv)를 사용하세요.

## 아직 필요한 provenance

현재 출력만으로는 최초 3D geometry의 출처와 입력 생성·최적화 과정을 재구성할 수 없습니다. 후속 계산에는 다음을 함께 추가하세요.

- 원본 `.inp` 파일
- geometry 출처 또는 생성 스크립트
- 정확한 ORCA 실행 명령과 실행 환경
- 입력·출력 SHA-256
- 사용한 ORCA 및 method별 권장 인용

ORCA 원본 출력에는 실행 시각, host, process ID, 작업 경로 같은 machine metadata가 포함될 수 있습니다. 외부 공유용 artifact를 만들 때는 과학적 결과를 바꾸지 않는 범위에서 해당 metadata를 별도로 정리하세요.

