# Firestore 데이터 구조 설계

## 📊 개요

MariaDB의 관계형 데이터 구조를 Firestore의 NoSQL 구조로 변환합니다.

## 🗂️ 전체 구조

```
firestore/
├── stocks/                          # 주식 데이터
│   └── {code}/                      # 종목코드별 문서
│       ├── info                     # 종목 기본 정보
│       ├── dividends                # 배당 정보
│       └── daily/                   # 일별 데이터 서브컬렉션
│           └── {date}               # 날짜별 문서
│
├── users/                           # 사용자 데이터
│   └── {userId}/                    # 사용자별 문서
│       └── lines/                   # 가로선 서브컬렉션
│           └── {lineId}             # 가로선별 문서
│
└── metadata/                        # 메타데이터
    └── lastUpdate                   # 마지막 업데이트 정보
```

## 📁 컬렉션 상세

### 1. stocks/{code}

**문서 구조**:
```javascript
{
  // 기본 정보 (stock_info 테이블)
  code: "005930",           // 종목코드
  name: "삼성전자",         // 종목명
  period: "월말",           // 월중/월말
  
  // 배당 정보 (dividend 테이블)
  dividends: [
    {
      date: "2024-03-29",   // 배당락일
      price: 361            // 배당금
    },
    {
      date: "2024-06-28",
      price: 361
    }
  ],
  
  // 메타데이터
  updated_at: Timestamp,    // 마지막 업데이트
  created_at: Timestamp     // 최초 생성
}
```

**인덱스**:
- `code` (자동)
- `name`
- `updated_at`

---

### 2. stocks/{code}/daily/{date}

**서브컬렉션**: 일별 주가 데이터 (stock 테이블)

**문서 구조**:
```javascript
{
  date: "2024-11-04",       // 날짜
  open: 58000,              // 시가
  high: 58500,              // 고가
  low: 57800,               // 저가
  close: 58200,             // 종가
  volume: 12345678,         // 거래량
  
  timestamp: Timestamp      // Firestore 타임스탬프
}
```

**인덱스**:
- `date` (자동)
- `timestamp`

**쿼리 예시**:
```javascript
// 최근 30일 데이터
db.collection('stocks/005930/daily')
  .orderBy('date', 'desc')
  .limit(30)
  .get()

// 특정 기간
db.collection('stocks/005930/daily')
  .where('date', '>=', '2024-01-01')
  .where('date', '<=', '2024-12-31')
  .get()

// 증분 동기화
db.collection('stocks/005930/daily')
  .where('timestamp', '>', lastSyncTime)
  .get()
```

---

### 3. users/{userId}

**문서 구조**:
```javascript
{
  email: "user@example.com",  // 이메일 (선택)
  displayName: "사용자1",      // 표시 이름
  created_at: Timestamp,
  last_login: Timestamp,
  
  // 설정
  settings: {
    theme: "dark",             // 테마
    defaultStocks: [           // 기본 종목
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

---

### 4. users/{userId}/lines/{lineId}

**서브컬렉션**: 사용자별 가로선 (horizontal 테이블)

**문서 구조**:
```javascript
{
  stockCode: "005930",      // 종목코드
  price: 58000,             // 가격
  color: "#FF0000",         // 색상
  lineStyle: "solid",       // 선 스타일 (solid, dashed, dotted)
  lineWidth: 2,             // 선 두께
  memo: "매수 목표가",      // 메모
  
  created_at: Timestamp,
  updated_at: Timestamp
}
```

**인덱스**:
- `stockCode`
- `created_at`

**쿼리 예시**:
```javascript
// 특정 종목의 가로선들
db.collection('users/user1/lines')
  .where('stockCode', '==', '005930')
  .orderBy('price', 'desc')
  .get()
```

---

### 5. metadata/lastUpdate

**단일 문서**: 전체 시스템 메타데이터 (data_time 테이블)

**문서 구조**:
```javascript
{
  // 종목별 마지막 업데이트 시간
  stocks: {
    "005930": Timestamp,
    "000660": Timestamp,
    // ...
  },
  
  // 전체 업데이트 정보
  lastSuccessfulUpdate: Timestamp,
  lastAttemptedUpdate: Timestamp,
  updateStatus: "success",      // success, failed, in_progress
  
  // 통계
  totalStocks: 50,
  totalRecords: 125000,
  
  // Cloud Function 실행 로그
  lastExecutionLog: {
    timestamp: Timestamp,
    duration: 12.5,             // 초
    recordsUpdated: 50,
    errors: []
  }
}
```

---

## 🔄 MariaDB → Firestore 매핑

### stock 테이블
```
MariaDB:
stock(code, date, open, high, low, close, volume)

Firestore:
stocks/{code}/daily/{date}
{
  open, high, low, close, volume, timestamp
}
```

### dividend 테이블
```
MariaDB:
dividend(code, date, price)

Firestore:
stocks/{code}
{
  dividends: [{date, price}, ...]
}
```

### stock_info 테이블
```
MariaDB:
stock_info(code, name, period)

Firestore:
stocks/{code}
{
  name, period
}
```

### horizontal 테이블
```
MariaDB:
horizontal(id, stockcode, price, color, ...)

Firestore:
users/{userId}/lines/{lineId}
{
  stockCode, price, color, ...
}
```

### data_time 테이블
```
MariaDB:
data_time(code, time, data_time)

Firestore:
metadata/lastUpdate
{
  stocks: {code: timestamp}
}
```

---

## 📊 데이터 크기 추정

### 문서당 크기

**stocks/{code}**:
```
종목 정보: ~200 bytes
배당 정보: ~100 bytes per entry × 4 = 400 bytes
총: ~600 bytes per 종목
```

**stocks/{code}/daily/{date}**:
```
일별 데이터: ~150 bytes
250 영업일/년 × 10년 = 2,500 문서
총: ~375 KB per 종목
```

**users/{userId}/lines/{lineId}**:
```
가로선: ~200 bytes per line
평균 10개 라인 = 2 KB per 사용자
```

### 전체 예상

```
50 종목:
- 종목 정보: 50 × 600 bytes = 30 KB
- 10년 데이터: 50 × 375 KB = 18.75 MB
- 사용자 데이터: 2 users × 2 KB = 4 KB
- 메타데이터: ~10 KB

총: ~19 MB (10년 후)
현재 (MariaDB 0.43MB와 유사): ~500 KB
```

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

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // 주식 기본 정보: 모두 읽기 가능
    match /stocks/{code} {
      allow read: if true;
      allow write: if false;  // Cloud Function만
    }
    
    // 일별 데이터: 모두 읽기 가능
    match /stocks/{code}/daily/{date} {
      allow read: if true;
      allow write: if false;  // Cloud Function만
    }
    
    // 사용자 데이터: 본인만 접근
    match /users/{userId} {
      allow read, write: if request.auth != null 
                         && request.auth.uid == userId;
      
      // 사용자의 가로선
      match /lines/{lineId} {
        allow read, write: if request.auth != null 
                           && request.auth.uid == userId;
      }
    }
    
    // 메타데이터: 모두 읽기 가능
    match /metadata/{document} {
      allow read: if true;
      allow write: if false;  // Cloud Function만
    }
  }
}
```

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
