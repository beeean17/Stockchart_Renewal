# Firestore 데이터 구조 설계

## 📊 개요

MariaDB의 관계형 데이터 구조를 Firestore의 NoSQL 구조로 변환합니다.

## 🗂️ 전체 구조

```
firestore/
├── stocks/                          # 주식 데이터
│   └── {code}/                      # 종목코드별 문서
│       ├── (문서 필드)
│       │   ├── code                 # 종목코드
│       │   ├── name                 # 종목명
│       │   ├── period               # 월중/월말
│       │   ├── latest               # 최신 가격 정보
│       │   ├── dividends            # 배당 정보 (배열)
│       │   ├── recent               # 최근 90일 데이터 (배열)
│       │   ├── updated_at           # 마지막 업데이트 시간
│       │   └── created_at           # 최초 생성 시간
│       │
│       └── monthly/                 # 월별 데이터 서브컬렉션
│           └── {YYYY-MM}/           # 월별 문서
│               ├── days             # 해당 월의 일별 데이터 (배열)
│               └── updated_at       # 월 데이터 업데이트 시간
│
├── users/                           # 사용자 데이터 (인증 기반)
│   └── {userId}/                    # Firebase Auth UID
│       ├── email                    # 이메일
│       ├── displayName              # 표시 이름
│       ├── photoURL                 # 프로필 사진
│       ├── created_at               # 계정 생성
│       ├── last_login               # 마지막 로그인
│       │
│       └── lines/                   # 가로선 서브컬렉션 (실시간 동기화)
│           └── {lineId}/            # 가로선별 문서
│               ├── stockCode        # 종목코드
│               ├── price            # 가격
│               ├── color            # 색상
│               ├── style            # 선 스타일
│               ├── width            # 선 두께
│               ├── memo             # 메모
│               ├── created_at       # 생성 시간
│               └── updated_at       # 수정 시간
│
└── metadata/                        # 메타데이터
    └── system/                      # 시스템 정보
        ├── lastUpdate               # 전체 마지막 업데이트
        ├── lastSuccessfulUpdate     # 마지막 성공
        ├── lastAttemptedUpdate      # 마지막 시도
        ├── updateStatus             # 업데이트 상태
        ├── updateLog                # 업데이트 로그
        └── stats                    # 통계
```

## 📁 컬렉션 상세

### 1. stocks/{code}

**문서 구조**:
```javascript
{
  // 기본 정보
  code: "005930",                   // 종목코드
  name: "삼성전자",                 // 종목명
  period: "월말",                   // 월중/월말
  
  // 최신 정보 (리스트 표시용)
  latest: {
    price: 58200,                   // 최신 종가
    date: "2024-11-04",            // 날짜
    change: -0.5                    // 등락률
  },
  
  // 배당 정보 (배열로 별도 관리)
  dividends: [
    {
      date: "2024-03-29",          // 배당락일
      price: 361                    // 배당금
    },
    {
      date: "2024-06-28",
      price: 361
    }
  ],
  
  // 최근 90일 데이터 (빠른 초기 로딩용)
  recent: [
    {
      date: "2024-11-04",
      o: 58100,                     // 시가
      h: 58500,                     // 고가
      l: 57800,                     // 저가
      c: 58200,                     // 종가
      v: 12345678                   // 거래량
    },
    // ... 최근 90일
  ],
  
  // 타임스탬프
  updated_at: Timestamp,            // 마지막 업데이트
  created_at: Timestamp             // 최초 생성
}
```

**인덱스**:
- `code` (자동)
- `name`
- `updated_at`

**읽기 효율**:
- 종목 문서 1개 읽기로 최근 90일 + 배당 전체 조회 가능
- 초기 로딩 시 1 read로 차트 표시

---

### 2. stocks/{code}/monthly/{YYYY-MM}

**서브컬렉션**: 월별 과거 데이터 (읽기 최적화)

**문서 구조**:
```javascript
{
  // 해당 월의 모든 일별 데이터 (배열)
  days: [
    {
      date: "2024-11-01",
      o: 58000,
      h: 58400,
      l: 57900,
      c: 58100,
      v: 11234567
    },
    {
      date: "2024-11-04",
      o: 58100,
      h: 58500,
      l: 57800,
      c: 58200,
      v: 12345678
    }
    // ... 해당 월의 모든 영업일
  ],
  
  // 타임스탬프
  updated_at: Timestamp             // 이 월의 마지막 업데이트
}
```

**인덱스**:
- 문서 ID (YYYY-MM 형식)

**장점**:
- 1년 데이터 = 12번 읽기 (일별 구조면 250번)
- 문서 크기: ~3.5KB (23일 × 150 bytes) < 1MB 제한 안전
- 월 단위 업데이트 효율적

**쿼리 예시**:
```
// 최근 1년 데이터 (12개월)
db.collection('stocks/005930/monthly')
  .orderBy('__name__', 'desc')
  .limit(12)
  .get()
// → 12 reads
```

---

### 3. users/{userId}

**userId**: Firebase Authentication UID (Google 로그인)

**문서 구조**:
```javascript
{
  // 구글 로그인 정보
  email: "user@gmail.com",          // 이메일
  displayName: "홍길동",            // 표시 이름
  photoURL: "https://...",          // 프로필 사진 URL
  
  // 타임스탬프
  created_at: Timestamp,            // 계정 생성
  last_login: Timestamp,            // 마지막 로그인
  
  // 설정 (선택)
  settings: {
    theme: "dark",                  // 테마
    defaultStocks: [                // 기본 종목
      "005930",
      "000660"
    ],
    chartSettings: {
      showVolume: true,
      showDividends: true,
      showMinMax: true
    }
  }
}
```

**접근 권한**:
- 읽기/쓰기: 본인만 (auth.uid == userId)

---

### 4. users/{userId}/lines/{lineId}

**서브컬렉션**: 사용자별 가로선 (horizontal 테이블) - **실시간 동기화**

**문서 구조**:
```javascript
{
  stockCode: "005930",              // 종목코드
  price: 58000,                     // 가격
  color: "#FF0000",                 // 색상
  style: "solid",                   // 선 스타일 (solid, dashed, dotted)
  width: 2,                         // 선 두께
  memo: "매수 목표가",              // 메모
  
  // 타임스탬프
  created_at: Timestamp,            // 생성 시간
  updated_at: Timestamp             // 수정 시간
}
```

**인덱스**:
- `stockCode`
- `created_at`

**접근 권한**:
- 읽기/쓰기: 본인만 (auth.uid == userId)
- 비로그인: 접근 불가

**실시간 동기화**:
- onSnapshot 리스너 사용
- 추가/수정/삭제 시 자동 반영
- 다른 기기에서도 즉시 동기화

**쿼리 예시**:
```
// 특정 종목의 가로선들
db.collection('users/user1/lines')
  .where('stockCode', '==', '005930')
  .orderBy('price', 'desc')
  .get()
```

---

### 5. metadata/system

**단일 문서**: 전체 시스템 메타데이터 (data_time 테이블)

**문서 구조**:
```javascript
{
  // 전체 업데이트 정보
  lastUpdate: Timestamp,                 // 마지막 업데이트 시간
  lastSuccessfulUpdate: Timestamp,       // 마지막 성공한 업데이트
  lastAttemptedUpdate: Timestamp,        // 마지막 시도 시간
  updateStatus: "success",               // success | failed | in_progress
  
  // 종목별 마지막 업데이트 시간 (선택)
  stocks: {
    "005930": Timestamp,
    "000660": Timestamp,
    // ...
  },
  
  // 업데이트 로그 (최근 30일)
  updateLog: {
    "2024-11-04": {
      success: true,
      timestamp: Timestamp,
      stocks_updated: 50,
      duration: 12.5,                    // 실행 시간 (초)
      errors: []
    },
    "2024-11-01": {
      success: true,
      timestamp: Timestamp,
      stocks_updated: 50,
      duration: 11.8,
      errors: []
    }
  },
  
  // 통계
  stats: {
    totalStocks: 50,                     // 전체 종목 수
    totalDays: 125000,                   // 전체 일별 데이터 수
    lastCalculated: Timestamp            // 통계 마지막 계산
  }
}
```

**접근 권한**:
- 읽기: 모두 가능
- 쓰기: Cloud Function만

**활용**:
- 앱 시작 시 데이터 신선도 확인
- 업데이트 실패 시 알림
- 시스템 상태 모니터링

---

## 🔄 MariaDB → Firestore 매핑

### stock 테이블 → 월별 구조로 변환
```
MariaDB:
stock(code, date, open, high, low, close, volume)

Firestore:
1. 최근 90일 → stocks/{code}/recent (배열)
2. 나머지 → stocks/{code}/monthly/{YYYY-MM}/days (배열)

변환 로직:
- date 기준으로 최근 90일과 그 이전 분리
- 이전 데이터는 월별로 그룹핑
- 각 월의 데이터를 days 배열에 저장
```

### dividend 테이블 → 배열로 통합
```
MariaDB:
dividend(code, date, price)

Firestore:
stocks/{code}/dividends (배열)

변환:
- 같은 종목의 배당을 배열로 합침
- 일별 데이터에는 포함하지 않음 (별도 관리)
```

### stock_info 테이블 → 종목 문서 필드
```
MariaDB:
stock_info(code, name, period)

Firestore:
stocks/{code}
{
  code, name, period, ...
}
```

### horizontal 테이블 → 사용자별 컬렉션
```
MariaDB:
horizontal(id, stockcode, price, color, ...)

Firestore:
users/{userId}/lines/{lineId}
{
  stockCode, price, color, ...
}

주의:
- MariaDB에는 userId 개념 없음
- 마이그레이션 시 기본 사용자 ID 할당 필요
- 또는 수동으로 사용자별 분리
```

### data_time 테이블 → metadata
```
MariaDB:
data_time(code, time, data_time)

Firestore:
metadata/system
{
  lastUpdate, 
  stocks: {code: timestamp}
}
```

---

## 📊 데이터 크기 추정

### 문서당 크기

**stocks/{code}** (종목 문서):
```
기본 정보: ~100 bytes
latest: ~50 bytes
dividends: ~30 bytes × 4회/년 = 120 bytes
recent (90일): ~150 bytes × 90 = 13.5 KB
타임스탬프: ~50 bytes

총: ~14 KB per 종목
```

**stocks/{code}/monthly/{YYYY-MM}** (월별 문서):
```
days 배열: ~150 bytes × 23일(평균) = 3.45 KB
타임스탬프: ~30 bytes

총: ~3.5 KB per 월
```

**users/{userId}/lines/{lineId}** (가로선):
```
가로선 데이터: ~200 bytes per line
평균 10개 = 2 KB per 사용자
```

### 전체 예상 (월별 구조 기준)

**현재 (0.43MB MariaDB)**:
```
50 종목:
- 종목 문서: 50 × 14 KB = 700 KB
- 월별 데이터 (현재까지): 50종목 × 평균 몇 개월 = 약 500 KB

총: ~1.2 MB
```

**10년 후 예상**:
```
50 종목:
- 종목 문서: 50 × 14 KB = 700 KB (recent 90일만)
- 월별 데이터: 50 × 120개월 × 3.5 KB = 21 MB
- 사용자 데이터: 2 users × 2 KB = 4 KB
- 메타데이터: ~10 KB

총: ~22 MB
```

**비교**:
- 일별 구조 예상: ~50 MB (250일/년 × 10년 × 50종목 × 150 bytes)
- 월별 구조 예상: ~22 MB
- **절감**: 약 56% 저장 공간 효율

---

## 🔍 쿼리 패턴

### 1. 차트 로드
```javascript
// 1년치 데이터
const querySnapshot = await db
  .collection('stocks/005930/daily')
  .orderBy('date', 'desc')
  .limit(250)
  .get();

const chartData = querySnapshot.docs.map(doc => ({
  time: doc.data().date,
  open: doc.data().open,
  high: doc.data().high,
  low: doc.data().low,
  close: doc.data().close,
  volume: doc.data().volume
}));
```

### 2. 실시간 업데이트
```javascript
// 특정 종목 실시간 감시
db.collection('stocks/005930/daily')
  .orderBy('date', 'desc')
  .limit(1)
  .onSnapshot(snapshot => {
    snapshot.docChanges().forEach(change => {
      if (change.type === 'added') {
        updateChart(change.doc.data());
      }
    });
  });
```

### 3. 증분 동기화
```javascript
// 마지막 동기화 이후 데이터만
const lastSync = await getLastSyncTime();

const newData = await db
  .collectionGroup('daily')  // 모든 종목의 daily
  .where('timestamp', '>', lastSync)
  .get();
```

### 4. 여러 종목 동시 조회
```javascript
// Batch Get (효율적)
const stockCodes = ['005930', '000660', '035420'];
const promises = stockCodes.map(code =>
  db.collection(`stocks/${code}/daily`)
    .orderBy('date', 'desc')
    .limit(30)
    .get()
);

const results = await Promise.all(promises);
```

---

## 🔐 보안 규칙

### Firestore Security Rules (인증 기반)

**핵심 원칙**:
1. 주식 데이터: 모두 읽기 가능, Cloud Function만 쓰기
2. 사용자 가로선: 본인만 접근 (로그인 필수)
3. 메타데이터: 모두 읽기 가능

**보안 규칙**:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // 주식 기본 정보: 모두 읽기 가능, Cloud Function만 쓰기
    match /stocks/{code} {
      allow read: if true;                // 비로그인도 가능
      allow write: if false;              // Cloud Function만
    }
    
    // 월별 데이터: 모두 읽기 가능, Cloud Function만 쓰기
    match /stocks/{code}/monthly/{month} {
      allow read: if true;                // 비로그인도 가능
      allow write: if false;              // Cloud Function만
    }
    
    // 사용자 문서: 본인만 접근
    match /users/{userId} {
      allow read, write: if request.auth != null 
                         && request.auth.uid == userId;
      
      // 가로선: 본인만 접근 (핵심!)
      match /lines/{lineId} {
        allow read, write: if request.auth != null 
                           && request.auth.uid == userId;
      }
    }
    
    // 메타데이터: 모두 읽기 가능
    match /metadata/{document} {
      allow read: if true;                // 비로그인도 가능
      allow write: if false;              // Cloud Function만
    }
  }
}
```

### 권한 매트릭스

| 리소스 | 비로그인 읽기 | 로그인 읽기 | 로그인 쓰기 | Cloud Function |
|--------|---------------|-------------|-------------|----------------|
| stocks/{code} | ✅ | ✅ | ❌ | ✅ 쓰기 가능 |
| stocks/{code}/monthly | ✅ | ✅ | ❌ | ✅ 쓰기 가능 |
| users/{userId} | ❌ | ✅ 본인만 | ✅ 본인만 | ❌ |
| users/{userId}/lines | ❌ | ✅ 본인만 | ✅ 본인만 | ❌ |
| metadata/system | ✅ | ✅ | ❌ | ✅ 쓰기 가능 |

### 보안 테스트

**테스트 시나리오**:
1. 비로그인 사용자가 차트 조회: ✅ 성공
2. 비로그인 사용자가 가로선 조회: ❌ 거부 (permission-denied)
3. 사용자 A가 본인 가로선 추가: ✅ 성공
4. 사용자 A가 사용자 B 가로선 조회: ❌ 거부
5. Cloud Function이 주식 데이터 업데이트: ✅ 성공

**Firebase Console에서 테스트**:
- Firestore Database → 규칙 → 규칙 시뮬레이터
- 각 시나리오별 테스트 수행

---

## 🚀 최적화 전략

### 1. 복합 인덱스
```
stocks/{code}/daily:
- date (desc), timestamp (desc)

users/{userId}/lines:
- stockCode (asc), price (desc)
```

### 2. 데이터 분할
- 너무 큰 배열은 서브컬렉션으로
- 예: 배당 데이터가 100개 이상이면 서브컬렉션 고려

### 3. 캐싱 전략
```javascript
// Offline persistence 활성화
firebase.firestore().enablePersistence()
  .catch(err => {
    if (err.code == 'failed-precondition') {
      // 여러 탭에서 열림
    } else if (err.code == 'unimplemented') {
      // 브라우저 미지원
    }
  });
```

---

## 📝 마이그레이션 스크립트 구조

```javascript
// MariaDB → Firestore 마이그레이션 의사코드

async function migrate() {
  // 1. stock_info + dividend → stocks/{code}
  const stocks = await mariadb.query('SELECT * FROM stock_info');
  for (const stock of stocks) {
    const dividends = await mariadb.query(
      'SELECT * FROM dividend WHERE code = ?',
      [stock.code]
    );
    
    await firestore.collection('stocks').doc(stock.code).set({
      code: stock.code,
      name: stock.name,
      period: stock.period,
      dividends: dividends.map(d => ({
        date: d.date,
        price: d.price
      })),
      created_at: FieldValue.serverTimestamp()
    });
  }
  
  // 2. stock → stocks/{code}/daily/{date}
  for (const stock of stocks) {
    const dailyData = await mariadb.query(
      'SELECT * FROM stock WHERE code = ?',
      [stock.code]
    );
    
    const batch = firestore.batch();
    dailyData.forEach(data => {
      const ref = firestore
        .collection('stocks')
        .doc(stock.code)
        .collection('daily')
        .doc(data.date);
      
      batch.set(ref, {
        date: data.date,
        open: data.open,
        high: data.high,
        low: data.low,
        close: data.close,
        volume: data.volume,
        timestamp: FieldValue.serverTimestamp()
      });
    });
    
    await batch.commit();
  }
  
  // 3. horizontal → users/{userId}/lines/{lineId}
  // 사용자 ID 매핑 필요
  
  // 4. data_time → metadata/lastUpdate
}
```

---

**다음 단계**: [마이그레이션 계획](MIGRATION_PLAN.md)
