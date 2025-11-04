# 마이그레이션 계획 및 로드맵

## 🎯 마이그레이션 전략

### 핵심 원칙
1. **병렬 운영**: 기존 시스템 유지하며 새 시스템 구축
2. **단계적 전환**: 한 번에 하나씩 검증
3. **롤백 가능**: 문제 발생 시 즉시 복구 가능
4. **무중단**: 사용자에게 영향 최소화

### 마이그레이션 흐름

```
[기존 시스템]                [새 시스템]
    │                           │
    │ ◄────────────────────────┤
    │    1. 데이터 복사          │
    │                           │
    │ ────────────────────────►│
    │    2. 병렬 운영/테스트     │
    │                           │
    │ ◄────────────────────────┤
    │    3. 검증 완료            │
    │                           │
    └─ [종료] ◄─────────────────┘
           4. 완전 전환
```

## 📅 전체 로드맵

### Week 1: 준비 단계
- **목표**: Firebase 환경 구축 및 기존 시스템 분석
- **소요 시간**: 3-5시간
- **산출물**: Firebase 프로젝트, 코드 분석 문서

### Week 2: 데이터 마이그레이션
- **목표**: MariaDB 데이터를 Firestore로 이전
- **소요 시간**: 2-4시간
- **산출물**: 완전히 마이그레이션된 Firestore DB

### Week 3: Cloud Function 개발
- **목표**: 한투 API 연동 자동화
- **소요 시간**: 4-6시간
- **산출물**: 작동하는 Cloud Function

### Week 4: React 앱 수정
- **목표**: Firestore 연동 및 기존 기능 이식
- **소요 시간**: 8-12시간
- **산출물**: 작동하는 웹 애플리케이션

### Week 5: 반응형 및 최적화
- **목표**: 모바일 최적화 및 성능 개선
- **소요 시간**: 6-8시간
- **산출물**: 반응형 웹 앱

### Week 6: 테스트 및 전환
- **목표**: 철저한 테스트 및 완전 전환
- **소요 시간**: 4-6시간
- **산출물**: 프로덕션 배포

### 추후 (선택): Android 웹뷰
- **목표**: 네이티브 앱 형태로 제공
- **소요 시간**: 2-3시간
- **산출물**: APK 파일

---

## 📋 Week 1: 준비 단계

### Day 1-2: Firebase 세팅

#### 1. Firebase 프로젝트 생성
**체크리스트**:
- [ ] Firebase Console 접속 (firebase.google.com)
- [ ] 새 프로젝트 생성
- [ ] 프로젝트 이름: "stock-chart-app" (예시)
- [ ] Google Analytics 설정 (선택)

#### 2. Firebase 서비스 활성화
**체크리스트**:
- [ ] Firestore Database 활성화
  - 위치: asia-northeast1 (서울) 또는 asia-northeast3 (오사카)
  - 모드: 프로덕션 (보안 규칙 나중에 설정)
- [ ] Firebase Hosting 활성화
- [ ] Cloud Functions 활성화
- [ ] Cloud Scheduler 활성화 (결제 정보 필요, Spark는 무료)

#### 3. 로컬 개발 환경
**체크리스트**:
- [ ] Node.js 설치 (v18 이상)
- [ ] Firebase CLI 설치: `npm install -g firebase-tools`
- [ ] Firebase 로그인: `firebase login`
- [ ] 프로젝트 초기화: `firebase init`
  - Firestore 선택
  - Functions 선택 (Python 또는 JavaScript)
  - Hosting 선택

### Day 3: 기존 시스템 분석

#### 1. FastAPI 코드 분석
**체크리스트**:
- [ ] 한투 API 호출 코드 위치 파악
- [ ] 사용 중인 라이브러리 확인 (`requirements.txt`)
- [ ] API 키 저장 방식 확인
- [ ] 스케줄링 로직 확인
- [ ] 데이터 변환 로직 확인

#### 2. React 코드 분석
**체크리스트**:
- [ ] 컴포넌트 구조 파악
- [ ] API 호출 위치 확인
- [ ] 상태 관리 방식 확인
- [ ] TradingView 차트 사용 방식 확인

#### 3. 데이터베이스 분석
**체크리스트**:
- [ ] MariaDB 연결 정보 확인
- [ ] 전체 데이터 양 확인 (쿼리 실행)
- [ ] 테이블 관계 파악
- [ ] 인덱스 확인

**확인용 SQL**:
```sql
-- 테이블별 행 수
SELECT 'stock' as table_name, COUNT(*) as count FROM stock
UNION ALL
SELECT 'dividend', COUNT(*) FROM dividend
UNION ALL
SELECT 'stock_info', COUNT(*) FROM stock_info
UNION ALL
SELECT 'horizontal', COUNT(*) FROM horizontal
UNION ALL
SELECT 'data_time', COUNT(*) FROM data_time;

-- 데이터 기간
SELECT 
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNT(DISTINCT code) as total_stocks
FROM stock;
```

---

## 📋 Week 2: 데이터 마이그레이션

### Day 1: 마이그레이션 스크립트 작성

#### 준비사항
**체크리스트**:
- [ ] Python 환경 준비
- [ ] 필요한 패키지 설치:
  ```bash
  pip install firebase-admin pymysql python-dotenv
  ```
- [ ] Firebase Admin SDK 키 다운로드
  - Firebase Console → 프로젝트 설정 → 서비스 계정
  - "새 비공개 키 생성" → JSON 파일 다운로드

#### 마이그레이션 스크립트 구조
```python
# migrate.py

import firebase_admin
from firebase_admin import credentials, firestore
import pymysql
from datetime import datetime

# 1. 연결 설정
# 2. stock_info + dividend → stocks/{code}
# 3. stock → stocks/{code}/daily/{date}
# 4. horizontal → users/{userId}/lines/{lineId}
# 5. data_time → metadata/lastUpdate
```

### Day 2: 마이그레이션 실행 및 검증

#### 실행 단계
**체크리스트**:
- [ ] 소량 테스트 (1-2 종목)
- [ ] 데이터 검증
- [ ] 전체 마이그레이션 실행
- [ ] 최종 검증

#### 검증 항목
**체크리스트**:
- [ ] 종목 수 일치
- [ ] 일별 데이터 수 일치
- [ ] 배당 데이터 정확성
- [ ] 날짜 범위 확인
- [ ] 가로선 데이터 확인

**검증용 코드**:
```python
# verify.py

def verify_migration():
    # MariaDB에서 카운트
    mariadb_count = get_mariadb_count()
    
    # Firestore에서 카운트
    firestore_count = get_firestore_count()
    
    # 비교
    assert mariadb_count == firestore_count
    print("✅ 마이그레이션 성공!")
```

---

## 📋 Week 3: Cloud Function 개발

### Day 1-2: Cloud Function 기본 구조

#### 1. Python Cloud Function 생성
**체크리스트**:
- [ ] functions 디렉토리 생성
- [ ] `main.py` 작성
- [ ] `requirements.txt` 작성
- [ ] 환경 변수 설정

#### 2. 한투 API 연동
**체크리스트**:
- [ ] 기존 FastAPI 로직 이식
- [ ] API 키 환경 변수로 관리
- [ ] 에러 핸들링 추가
- [ ] 로깅 추가

### Day 3: 스케줄링 및 배포

#### 1. Cloud Scheduler 설정
**체크리스트**:
- [ ] 스케줄 생성: `40 15 * * 1-5`
- [ ] 타임존: Asia/Seoul
- [ ] 타겟: Cloud Function

#### 2. 배포 및 테스트
**체크리스트**:
- [ ] 로컬 테스트
- [ ] Cloud Function 배포: `firebase deploy --only functions`
- [ ] 수동 실행 테스트
- [ ] 스케줄 실행 대기 (다음날 15:40)
- [ ] 로그 확인

---

## 📋 Week 4: React 앱 수정

### Day 1-2: Firebase SDK 통합

#### 1. 패키지 설치 및 설정
**체크리스트**:
- [ ] Firebase SDK 설치
  ```bash
  npm install firebase
  ```
- [ ] Firebase 초기화 코드 작성 (`src/firebase.js`)
- [ ] 환경 변수 설정 (`.env`)

#### 2. Firestore 연동
**체크리스트**:
- [ ] 기존 API 호출 제거
- [ ] Firestore 쿼리로 대체
- [ ] 실시간 리스너 추가 (선택)
- [ ] 로컬 캐싱 활성화

### Day 3-4: 기능 이식

#### 1. 차트 데이터 로딩
**체크리스트**:
- [ ] 종목 선택 시 데이터 로드
- [ ] TradingView 차트 연동
- [ ] 배당 마커 표시
- [ ] 거래량 차트 표시

#### 2. 사용자 기능
**체크리스트**:
- [ ] 가로선 저장/수정/삭제
- [ ] 사이드바 토글
- [ ] 차트 요소 토글
- [ ] 설정 저장

#### 3. 테스트
**체크리스트**:
- [ ] 로컬 개발 서버: `npm start`
- [ ] 모든 기능 작동 확인
- [ ] 버그 수정

---

## 📋 Week 5: 반응형 및 최적화

### Day 1-2: 반응형 디자인

#### 1. Tailwind CSS 설치 (선택)
**체크리스트**:
- [ ] Tailwind 설치 및 설정
- [ ] 기존 CSS 변환
- [ ] 반응형 클래스 적용

#### 2. 레이아웃 조정
**체크리스트**:
- [ ] Desktop 레이아웃
- [ ] Mobile 레이아웃
- [ ] 브레이크포인트 설정
- [ ] 사이드바 모바일 처리 (햄버거 메뉴)

### Day 3: 모바일 최적화

#### 터치 제스처
**체크리스트**:
- [ ] 차트 핀치 줌
- [ ] 스와이프 네비게이션
- [ ] 터치 가로선 조작

#### 성능 최적화
**체크리스트**:
- [ ] 이미지 최적화
- [ ] 코드 스플리팅
- [ ] Lazy loading
- [ ] 번들 크기 확인

---

## 📋 Week 6: 테스트 및 전환

### Day 1-2: 테스트

#### 기능 테스트
**체크리스트**:
- [ ] 모든 종목 로드 테스트
- [ ] 차트 인터랙션 테스트
- [ ] 가로선 CRUD 테스트
- [ ] 배당 표시 테스트
- [ ] 거래량 표시 테스트

#### 크로스 브라우저 테스트
**체크리스트**:
- [ ] Chrome (Desktop)
- [ ] Firefox (Desktop)
- [ ] Edge (Desktop)
- [ ] Chrome (Mobile)
- [ ] Safari (Mobile, iOS - 선택)

#### 성능 테스트
**체크리스트**:
- [ ] Lighthouse 점수 확인
- [ ] 로딩 속도 측정
- [ ] Firestore 읽기/쓰기 횟수 확인

### Day 3: 배포 및 전환

#### 1. Firebase Hosting 배포
**체크리스트**:
- [ ] 프로덕션 빌드: `npm run build`
- [ ] Firebase 배포: `firebase deploy --only hosting`
- [ ] URL 확인
- [ ] SSL 인증서 확인 (자동)

#### 2. DNS 설정 (선택)
**체크리스트**:
- [ ] 커스텀 도메인 추가
- [ ] DNS 레코드 설정
- [ ] SSL 인증서 대기

#### 3. 사용자 테스트
**체크리스트**:
- [ ] 2명 모두 접속 테스트
- [ ] 데이터 정확성 확인
- [ ] 기능 동작 확인
- [ ] 피드백 수집

#### 4. 최종 전환
**체크리스트**:
- [ ] 기존 시스템과 병렬 운영 (1-2주)
- [ ] 문제 없음 확인
- [ ] 기존 시스템 종료
- [ ] 기존 서버 정리

---

## 📋 추후: Android 웹뷰 (선택)

### 필요성 판단
- 브라우저로 충분한가?
- 앱 형태가 필요한가?
- 설치 편의성이 중요한가?

### 구현 (필요 시)
**체크리스트**:
- [ ] Android Studio 설치
- [ ] 빈 프로젝트 생성
- [ ] WebView 설정
- [ ] 권한 설정 (인터넷)
- [ ] 빌드 및 테스트
- [ ] APK 생성
- [ ] 직접 설치 (2명)

---

## 🔄 롤백 계획

### 단계별 롤백 전략

#### Week 2-3 (데이터/Function)
- **문제**: 마이그레이션 오류, Function 실패
- **롤백**: 기존 시스템 그대로 유지
- **영향**: 없음 (아직 전환 안 함)

#### Week 4-5 (React 개발)
- **문제**: React 앱 버그, 기능 누락
- **롤백**: 기존 React 앱 사용
- **영향**: 없음 (병렬 개발)

#### Week 6 (배포 후)
- **문제**: 프로덕션 이슈
- **롤백**: 
  1. Firebase Hosting에서 이전 버전 복원
  2. 또는 기존 시스템 재가동
- **영향**: 최소 (빠른 복구)

---

## 📊 체크포인트

### 각 단계 완료 기준

#### Week 1 완료
- [x] Firebase 프로젝트 생성됨
- [x] 로컬 개발 환경 구축됨
- [x] 기존 시스템 분석 완료

#### Week 2 완료
- [x] 모든 데이터 Firestore에 마이그레이션됨
- [x] 데이터 검증 완료
- [x] 백업 완료

#### Week 3 완료
- [x] Cloud Function 배포됨
- [x] 스케줄러 작동 확인됨
- [x] 데이터 자동 수집 확인됨

#### Week 4 완료
- [x] React 앱이 Firestore 연동됨
- [x] 모든 기존 기능 작동함
- [x] 로컬 테스트 통과

#### Week 5 완료
- [x] 반응형 디자인 적용됨
- [x] 모바일에서 정상 작동
- [x] 성능 최적화 완료

#### Week 6 완료
- [x] 프로덕션 배포됨
- [x] 2명 사용자 테스트 완료
- [x] 기존 시스템 종료됨

---

## 🎯 성공 지표

### 기술적 지표
- [ ] Firestore 읽기: <1,000회/일
- [ ] Firestore 쓰기: <100회/일
- [ ] Cloud Function 실행 성공률: >99%
- [ ] 웹 앱 로딩 시간: <3초
- [ ] Lighthouse 점수: >90

### 사용자 지표
- [ ] 모든 기능 작동
- [ ] 데이터 정확성 100%
- [ ] 사용자 만족도: 높음
- [ ] 버그 보고: 0건 (심각)

---

## 📝 마이그레이션 로그

### 진행 상황 추적

```markdown
## 2025-11-04
- [x] 마이그레이션 계획 수립
- [ ] Firebase 프로젝트 생성

## 2025-11-XX
- [ ] 데이터 마이그레이션 시작
...
```

---

**다음 단계**: [구현 가이드](IMPLEMENTATION_GUIDE.md)
