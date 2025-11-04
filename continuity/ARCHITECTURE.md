# 새로운 아키텍처 설계

## 🎯 설계 목표

1. **서버리스**: 서버 관리 불필요
2. **자동화**: 디바이스 독립적 데이터 수집
3. **크로스 플랫폼**: Desktop + Mobile 지원
4. **무료**: Firebase Spark Plan 활용
5. **간소화**: 단일 코드베이스

## 🏗️ 전체 아키텍처

```
┌────────────────────────────────────┐
│   Firebase Cloud Scheduler         │
│   (매일 15:40 KST)                 │
└────────────┬───────────────────────┘
             │ Trigger
             ↓
┌────────────────────────────────────┐
│   Firebase Cloud Functions         │
│   (Python/Node.js)                 │
│   - 한투 REST API 호출             │
│   - 데이터 변환/처리                │
│   - Firestore 저장                 │
└────────────┬───────────────────────┘
             │ Write
             ↓
┌────────────────────────────────────┐
│   Firebase Firestore               │
│   (NoSQL Database)                 │
│   - stocks/                        │
│   - users/                         │
│   - metadata/                      │
└────────────┬───────────────────────┘
             │ Read/Subscribe
             ↓
┌────────────────────────────────────┐
│   React Web Application            │
│   (Firebase Hosting)               │
│   - TradingView Charts             │
│   - 반응형 디자인                  │
│   - Firestore SDK                  │
└────────┬───────────┬───────────────┘
         │           │
    ┌────┴────┐ ┌────┴──────┐
    │ Desktop │ │  Android  │
    │(Browser)│ │ (WebView) │
    └─────────┘ └───────────┘
```

## 🔧 기술 스택

### Backend (Firebase)

#### 1. Cloud Functions
**역할**: 서버 로직 실행
- **언어**: Python (권장) 또는 Node.js
- **트리거**: 
  - Cloud Scheduler (매일 15:40)
  - HTTP 엔드포인트 (선택사항)
- **주요 작업**:
  - 한투 API 호출
  - 데이터 가공
  - Firestore 저장

#### 2. Cloud Scheduler
**역할**: 정시 실행 스케줄링
- **스케줄**: `40 15 * * 1-5` (평일 15:40)
- **타임존**: Asia/Seoul
- **타겟**: Cloud Function

#### 3. Firestore
**역할**: NoSQL 데이터베이스
- **특징**:
  - 실시간 동기화
  - 오프라인 지원
  - 자동 스케일링
- **쿼리**: 
  - 복합 쿼리 지원
  - 인덱스 자동 생성

#### 4. Firebase Hosting
**역할**: 정적 웹 호스팅
- **특징**:
  - CDN 자동 배포
  - HTTPS 자동 적용
  - 빠른 글로벌 배포

### Frontend

#### 1. React (Create React App)
**역할**: UI 프레임워크
- **기존 코드 재사용**
- **추가**: Firebase SDK

#### 2. TradingView Lightweight Charts v5
**역할**: 차트 시각화
- **유지**: 기존과 동일
- **장점**: 고성능, 터치 제스처 지원

#### 3. Tailwind CSS
**역할**: 반응형 스타일링
- **추가 이유**: 쉬운 반응형 구현
- **대체 가능**: CSS Module, Styled Components

#### 4. Firebase SDK
**역할**: Firebase 서비스 연동
- **주요 모듈**:
  - `firebase/firestore`: 데이터베이스
  - `firebase/auth`: 인증 (선택)

### Mobile

#### Android WebView
**역할**: 웹앱을 네이티브 앱으로 래핑
- **언어**: Kotlin/Java
- **구성**: 매우 간단 (~50줄)
- **배포**: APK 직접 설치 (Play Store 불필요)

## 📊 데이터 흐름

### 1. 데이터 수집 (매일 15:40)

```
[Cloud Scheduler]
    ↓ Trigger
[Cloud Function 시작]
    ↓ 
[한투 API 호출]
    ↓ 종목별 데이터 요청
[데이터 수신]
    ↓ 변환/검증
[Firestore 저장]
    ├─ stocks/{code}/daily/{date}
    ├─ stocks/{code}/dividends
    └─ metadata/lastUpdate
    ↓
[완료]
```

### 2. 데이터 조회 (사용자 앱)

```
[React App 시작]
    ↓
[Firebase 초기화]
    ↓
[Firestore 쿼리]
    ├─ 초기 로드: 선택 종목 전체
    ├─ 증분 동기화: 변경된 데이터만
    └─ 실시간 리스너: 자동 업데이트
    ↓
[로컬 캐싱]
    ├─ IndexedDB
    └─ localStorage
    ↓
[TradingView 차트 렌더링]
```

### 3. 사용자 데이터 저장

```
[사용자 액션]
    ├─ 가로선 추가
    ├─ 메모 작성
    └─ 설정 변경
    ↓
[Firestore 저장]
    └─ users/{userId}/lines/{id}
    ↓
[실시간 동기화]
    └─ 다른 기기에도 즉시 반영
```

## 🔐 보안 및 인증

### Firebase Authentication (선택사항)

**현재**: 2명만 사용, 인증 불필요할 수도
**옵션**:
1. **인증 없음**: Firestore 규칙으로만 제어
2. **간단 인증**: 이메일/비밀번호
3. **소셜 로그인**: Google, Apple 등

### Firestore Security Rules

```javascript
// 예시: 인증 없이 읽기만 허용
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 주식 데이터: 모두 읽기 가능
    match /stocks/{document=**} {
      allow read: if true;
      allow write: if false;  // Cloud Function만 쓰기
    }
    
    // 사용자 데이터: 인증된 사용자만
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null 
                         && request.auth.uid == userId;
    }
  }
}
```

### API 키 관리

```
Cloud Functions 환경 변수:
- KIS_APP_KEY
- KIS_APP_SECRET
- KIS_ACCOUNT_NO (필요시)

설정 방법:
firebase functions:config:set kis.app_key="YOUR_KEY"
```

## 📱 플랫폼별 구현

### Desktop

**접근 방법**:
```
https://your-project.web.app
```

**특징**:
- 브라우저로 직접 접속
- 북마크/즐겨찾기 추가
- PWA로 설치 가능 (선택)

### Mobile (Android)

**Option 1: 브라우저**
- Chrome/Samsung Internet
- 반응형 웹으로 최적화
- 별도 설치 불필요

**Option 2: WebView 앱 (권장)**
- 앱처럼 보임
- 홈 화면 아이콘
- 브라우저 UI 없음
- APK 직접 배포

### Mobile (iOS) - 제외
- 당분간 구현하지 않음
- 필요시 PWA로 대응 가능

## 🔄 동기화 전략

### 초기 로드
```
1. 사용자가 관심 종목 선택
2. 해당 종목의 전체 히스토리 다운로드
3. 로컬 캐시에 저장 (IndexedDB)
```

### 증분 동기화
```
1. 마지막 동기화 시간 확인
2. 그 이후 변경된 데이터만 쿼리
   - where('updated_at', '>', lastSyncTime)
3. 로컬 캐시 업데이트
```

### 실시간 업데이트 (선택)
```
1. Firestore onSnapshot() 리스너
2. 데이터 변경 시 자동 콜백
3. 차트 자동 업데이트
```

## 🎨 UI/UX 설계

### Desktop Layout
```
┌──────────────────────────────────────┐
│ Header: 종목명, 검색, 설정            │
├─────────┬────────────────────────────┤
│         │                            │
│ Sidebar │     TradingView Chart      │
│         │                            │
│ 종목    │     (가로선, 배당 표시)    │
│ 리스트  │                            │
│         │                            │
│         ├────────────────────────────┤
│         │   거래량 차트              │
└─────────┴────────────────────────────┘
```

### Mobile Layout
```
┌──────────────────────────┐
│ Header + 햄버거 메뉴      │
├──────────────────────────┤
│                          │
│   TradingView Chart      │
│   (풀스크린)             │
│                          │
│   (핀치줌, 스와이프)      │
│                          │
├──────────────────────────┤
│   거래량 (접이식)         │
└──────────────────────────┘

[메뉴 열림 시]
┌──────────────────────────┐
│ 종목 리스트              │
│ 설정                     │
│ 정보                     │
└──────────────────────────┘
```

## 🚀 성능 최적화

### 1. 데이터 로딩
- **Lazy Loading**: 필요한 종목만 로드
- **Pagination**: 차트 데이터 분할 로드
- **Caching**: IndexedDB로 로컬 캐싱

### 2. 차트 렌더링
- **Virtual Scrolling**: 보이는 영역만 렌더링
- **Debouncing**: 연속 이벤트 제한
- **Web Workers**: 데이터 계산 분리

### 3. 네트워크
- **Batch Requests**: 여러 요청 묶기
- **Compression**: Firestore 자동 압축
- **CDN**: Firebase Hosting CDN 활용

## 🔧 확장 가능성

### 단기 (현재)
- 2명 사용
- 50종목
- 10년 히스토리

### 중기 (필요시)
- 10명 사용 → 인증 추가
- 100종목
- 실시간 알림

### 장기 (가능성)
- 100명+ → Blaze Plan
- 1000종목+
- 고급 분석 기능

## ⚠️ 제약사항 및 해결책

### 1. Firestore 쿼리 제한
**제약**: 복잡한 쿼리 어려움
**해결**: 데이터 구조 최적화, 클라이언트 필터링

### 2. Cold Start
**제약**: Cloud Function 첫 실행 느림 (1-2초)
**해결**: 
- Minimum instances 설정 (유료)
- 또는 수용 (2명 사용이라 무관)

### 3. Firestore 읽기 제한
**제약**: 50,000 reads/day (무료)
**해결**: 
- 로컬 캐싱 철저히
- 현재 사용량으로 충분

## 📊 모니터링

### Firebase Console
- Firestore 사용량
- Cloud Functions 실행 로그
- 에러 추적
- 성능 모니터링

### 알림 설정
- 할당량 80% 도달 시
- Cloud Function 실패 시
- 비정상적 트래픽 감지 시

---

**다음 단계**: [데이터 구조 설계](DATA_STRUCTURE.md)
