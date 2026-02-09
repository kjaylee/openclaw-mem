# openclaw-mem 벤치마크 결과

## 한국어 검색 정확도 검증

**날짜:** 2026-02-09  
**모델:** `intfloat/multilingual-e5-small` (384 dim, ~470MB)  
**백엔드:** local (sentence-transformers)  
**환경:** Mac Studio (M-series, arm64), Python 3.14

### 결과 요약

| 지표 | 결과 | 기준 | 판정 |
|------|------|------|------|
| **정확도** | **10/10 (100%)** | ≥ 80% | ✅ 통과 |
| **평균 응답시간** | **0.38s** | ≤ 1.0s | ✅ 통과 |
| **인덱싱 시간** | 31.88s | - | 첫 로드 포함 |
| **청크 수** | 6 | - | 5개 섹션 + 헤더 |

### 테스트 데이터

한국어 + 영어 혼합 프로젝트 기억 데이터 (805 bytes, 5개 섹션):
- 게임 개발, 삼국지 프로젝트, 소설 파이프라인, 인프라, 보안

### 질의별 상세 결과

| # | 질의 | 언어 | Top Score | 시간 | 결과 |
|---|------|------|-----------|------|------|
| Q1 | 삼국지 초상화 진행률 | 🇰🇷 | 0.8782 | 1.554s* | ✅ |
| Q2 | 게임 몇 개 만들었지? | 🇰🇷 | 0.8495 | 0.403s | ✅ |
| Q3 | sprite sheet 추출 | 🇰🇷🇺🇸 | 0.8713 | 0.506s | ✅ |
| Q4 | 소설 스케줄 | 🇰🇷 | 0.8482 | 0.017s | ✅ |
| Q5 | 보안 취약점 | 🇰🇷 | 0.8489 | 0.395s | ✅ |
| Q6 | MiniPC에서 뭘 돌리고 있지? | 🇰🇷 | 0.8506 | 0.392s | ✅ |
| Q7 | Idle Hero | 🇺🇸 | 0.8329 | 0.484s | ✅ |
| Q8 | API key error | 🇺🇸 | 0.8523 | 0.014s | ✅ |
| Q9 | 한세진 작가 | 🇰🇷 | 0.8380 | 0.015s | ✅ |
| Q10 | ClawHub skills | 🇺🇸 | 0.8645 | 0.015s | ✅ |

*\* Q1 첫 쿼리는 LanceDB 초기화 포함*

### 핵심 발견

1. **한국어 검색 완벽 지원**: 순수 한국어 질의 (Q1, Q2, Q4, Q5, Q9) 모두 정확한 섹션 반환
2. **교차 언어 검색**: 한영 혼합 질의 (Q3, Q6) 정상 작동
3. **영어 질의**: 영어 키워드 (Q7, Q8, Q10) 한국어 문서에서 정확히 매칭
4. **유사도 점수**: 0.83~0.88 범위로 안정적 (cosine distance 기준)
5. **캐시 효과**: 첫 쿼리 후 응답시간 급감 (1.5s → 0.01~0.5s)

### 재현 방법

```bash
cd openclaw-mem
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

export OPENCLAW_MEM_BACKEND=local
export OPENCLAW_MEM_MODEL=intfloat/multilingual-e5-small
export OPENCLAW_MEM_ROOT=/tmp/bench-test
export OPENCLAW_MEM_DB_PATH=/tmp/bench-test/lance_db

# 인덱싱
openclaw-mem index /tmp/bench-test/memory/memory.md

# 검색 예시
openclaw-mem search "삼국지 초상화 진행률" --raw
openclaw-mem search "API key error" --raw
```
