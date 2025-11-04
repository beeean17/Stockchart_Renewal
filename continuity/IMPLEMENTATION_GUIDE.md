# 단계별 구현 가이드

## 📌 이 문서의 목적

실제 코딩과 구현 시 참고할 구체적인 가이드입니다. 각 단계별로 **무엇을 해야 하는지**, **어떻게 하는지**를 상세히 설명합니다.

---

## 🔧 Phase 1: Firebase 프로젝트 설정

### 1-1. Firebase Console 설정

#### Firebase 프로젝트 생성
1. https://console.firebase.google.com 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력 (예: `stock-chart-app`)
4. Google Analytics 설정 (선택사항)
5. 프로젝트 생성 완료

#### Firestore Database 활성화
1. 왼쪽 메뉴 → "Firestore Database"
2. "데이터베이스 만들기" 클릭
3. 위치 선택: `asia-northeast1` (서울) 또는 `asia-northeast3` (오사카)
4. 보안 규칙: "프로덕션 모드"로 시작
5. 완료

#### Firebase Hosting 활성화
1. 왼쪽 메뉴 → "Hosting"
2. "시작하기" 클릭
3. CLI 설치 안내 확인

#### Cloud Functions 활성화
1. 왼쪽 메뉴 → "Functions"
2. "시작하기" 클릭
3. Blaze 플랜 안내 (무료 할당량 충분)

### 1-2. 로컬 개발 환경 설정

#### Node.js 설치
```bash
# Node.js 18 이상 설치 확인
node --version

# 없으면 https://nodejs.org에서 다운로드
```

#### Firebase CLI 설치
```bash
npm install -g firebase-tools

# 버전 확인
firebase --version
```

#### Firebase 로그인
```bash
firebase login

# 브라우저에서 Google 계정으로 로그인
```

#### 프로젝트 초기화
```bash
# 프로젝트 디렉토리 생성
mkdir stock-chart-firebase
cd stock-chart-firebase

# Firebase 초기화
firebase init

# 선택 항목:
# [x] Firestore
# [x] Functions (Python 또는 JavaScript 선택)
# [x] Hosting

# 프로젝트 선택: 위에서 만든 프로젝트
```

#### 디렉토리 구조 확인
```
stock-chart-firebase/
├── functions/              # Cloud Functions 코드
│   ├── main.py            # Python 선택 시
│   └── requirements.txt
├── public/                # 정적 파일 (나중에 React 빌드 결과물)
├── firestore.rules        # Firestore 보안 규칙
├── firestore.indexes.json # Firestore 인덱스
└── firebase.json          # Firebase 설정
```

---

## 🗄️ Phase 2: 데이터 마이그레이션

### 2-1. Firebase Admin SDK 설정

#### 서비스 계정 키 생성
1. Firebase Console → 프로젝트 설정 → 서비스 계정
2. "새 비공개 키 생성" 클릭
3. JSON 파일 다운로드
4. 파일명: `serviceAccountKey.json`
5. 프로젝트 루트에 저장 (`.gitignore`에 추가!)

#### 마이그레이션 스크립트 준비
```bash
# 별도 디렉토리 생성
mkdir migration
cd migration

# Python 환경 생성 (선택)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 필요한 패키지 설치
pip install firebase-admin pymysql python-dotenv
```

### 2-2. 마이그레이션 스크립트 작성

#### `.env` 파일 생성
```env
# MariaDB 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=stock_db

# Firebase
FIREBASE_KEY_PATH=../serviceAccountKey.json
```

#### `migrate.py` 스크립트 개요

**주요 함수**:
1. `connect_mariadb()`: MariaDB 연결
2. `connect_firestore()`: Firestore 연결
3. `migrate_stock_info()`: 종목 정보 마이그레이션
4. `migrate_daily_data()`: 일별 데이터 마이그레이션
5. `migrate_horizontal_lines()`: 가로선 마이그레이션
6. `migrate_metadata()`: 메타데이터 마이그레이션
7. `verify()`: 검증

#### 실행 전 체크리스트
- [ ] MariaDB 연결 확인
- [ ] Firebase Admin SDK 키 확인
- [ ] 소량 테스트 (1-2 종목)
- [ ] 데이터 백업 완료

#### 실행
```bash
# 테스트 모드 (소량)
python migrate.py --test --stocks 2

# 전체 마이그레이션
python migrate.py --full

# 검증
python migrate.py --verify
```

### 2-3. 데이터 검증

#### Firestore Console에서 확인
1. Firebase Console → Firestore Database
2. 컬렉션 확인:
   - `stocks/`: 종목 수 확인
   - `stocks/{code}/daily`: 일별 데이터 확인
   - `metadata/lastUpdate`: 메타데이터 확인

#### 쿼리로 검증
```python
# verify.py

def verify_counts():
    # MariaDB 카운트
    mariadb_stocks = execute_query("SELECT COUNT(DISTINCT code) FROM stock")
    mariadb_daily = execute_query("SELECT COUNT(*) FROM stock")
    
    # Firestore 카운트
    firestore_stocks = len(list(db.collection('stocks').stream()))
    
    firestore_daily = 0
    for stock in db.collection('stocks').stream():
        daily_docs = stock.reference.collection('daily').stream()
        firestore_daily += len(list(daily_docs))
    
    print(f"MariaDB: {mariadb_stocks} stocks, {mariadb_daily} daily records")
    print(f"Firestore: {firestore_stocks} stocks, {firestore_daily} daily records")
    
    assert mariadb_stocks == firestore_stocks
    assert mariadb_daily == firestore_daily
    print("✅ 검증 성공!")
```

---

## ☁️ Phase 3: Cloud Function 개발

### 3-1. Cloud Function 구조

#### `functions/main.py` (Python 예시)

**주요 컴포넌트**:
1. 한투 API 클라이언트
2. 데이터 수집 로직
3. Firestore 저장 로직
4. 에러 핸들링
5. 로깅

#### 환경 변수 설정
```bash
# Firebase Functions 환경 변수 설정
firebase functions:config:set \
  kis.app_key="YOUR_APP_KEY" \
  kis.app_secret="YOUR_APP_SECRET"

# 확인
firebase functions:config:get
```

#### `requirements.txt` (Python)
```
firebase-admin==6.2.0
requests==2.31.0
python-dotenv==1.0.0
```

### 3-2. 로컬 테스트

#### Firebase Emulator Suite 사용
```bash
# Emulator 설치
firebase init emulators

# 선택:
# [x] Functions
# [x] Firestore

# Emulator 실행
firebase emulators:start

# 별도 터미널에서 함수 테스트
curl http://localhost:5001/PROJECT_ID/REGION/fetchStockData
```

### 3-3. Cloud Scheduler 설정

#### Console에서 설정
1. Google Cloud Console → Cloud Scheduler
2. "일정 만들기" 클릭
3. 설정:
   - 이름: `daily-stock-fetch`
   - 빈도: `40 15 * * 1-5`
   - 시간대: `Asia/Seoul`
   - 대상: Cloud Functions
   - 함수: `fetchStockData`

#### 또는 CLI로 설정
```bash
# gcloud CLI 설치 필요
gcloud scheduler jobs create http daily-stock-fetch \
  --schedule="40 15 * * 1-5" \
  --time-zone="Asia/Seoul" \
  --uri="https://REGION-PROJECT_ID.cloudfunctions.net/fetchStockData" \
  --http-method=GET
```

### 3-4. 배포

```bash
# Cloud Function만 배포
firebase deploy --only functions

# 특정 함수만 배포
firebase deploy --only functions:fetchStockData
```

#### 배포 후 확인
1. Firebase Console → Functions
2. 함수 목록 확인
3. 로그 확인
4. 수동 실행 테스트

---

## ⚛️ Phase 4: React 앱 수정

### 4-1. Firebase SDK 통합

#### 패키지 설치
```bash
cd your-react-app

npm install firebase
```

#### `src/firebase.js` 생성

**Firebase 초기화 코드**:
```javascript
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
```

#### `.env` 파일 생성
```env
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
```

> **참고**: Firebase Console → 프로젝트 설정 → 앱 추가 → 웹에서 설정 값 확인

### 4-2. Firestore 데이터 로딩

#### 종목 리스트 로드
```javascript
import { collection, getDocs } from 'firebase/firestore';
import { db } from './firebase';

async function loadStocks() {
  const stocksRef = collection(db, 'stocks');
  const snapshot = await getDocs(stocksRef);
  
  const stocks = snapshot.docs.map(doc => ({
    code: doc.id,
    ...doc.data()
  }));
  
  return stocks;
}
```

#### 차트 데이터 로드
```javascript
import { collection, query, orderBy, limit, getDocs } from 'firebase/firestore';

async function loadChartData(stockCode, days = 250) {
  const dailyRef = collection(db, `stocks/${stockCode}/daily`);
  const q = query(
    dailyRef,
    orderBy('date', 'desc'),
    limit(days)
  );
  
  const snapshot = await getDocs(q);
  
  const chartData = snapshot.docs
    .map(doc => doc.data())
    .reverse(); // 오래된 것부터
  
  return chartData;
}
```

#### 실시간 업데이트 (선택)
```javascript
import { onSnapshot, query, orderBy, limit } from 'firebase/firestore';

function subscribeToUpdates(stockCode, callback) {
  const dailyRef = collection(db, `stocks/${stockCode}/daily`);
  const q = query(
    dailyRef,
    orderBy('date', 'desc'),
    limit(1)
  );
  
  return onSnapshot(q, snapshot => {
    snapshot.docChanges().forEach(change => {
      if (change.type === 'added') {
        callback(change.doc.data());
      }
    });
  });
}
```

### 4-3. 가로선 저장/로드

#### 가로선 저장
```javascript
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

async function saveHorizontalLine(userId, lineData) {
  const linesRef = collection(db, `users/${userId}/lines`);
  
  await addDoc(linesRef, {
    ...lineData,
    created_at: serverTimestamp(),
    updated_at: serverTimestamp()
  });
}
```

#### 가로선 로드
```javascript
import { collection, query, where, getDocs } from 'firebase/firestore';

async function loadHorizontalLines(userId, stockCode) {
  const linesRef = collection(db, `users/${userId}/lines`);
  const q = query(
    linesRef,
    where('stockCode', '==', stockCode)
  );
  
  const snapshot = await getDocs(q);
  
  return snapshot.docs.map(doc => ({
    id: doc.id,
    ...doc.data()
  }));
}
```

### 4-4. TradingView 차트 통합

#### 차트 초기화
```javascript
import { createChart } from 'lightweight-charts';
import { useEffect, useRef } from 'react';

function StockChart({ stockCode }) {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  
  useEffect(() => {
    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 600,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
    });
    
    chartRef.current = chart;
    
    // 캔들스틱 시리즈 추가
    const candlestickSeries = chart.addCandlestickSeries();
    
    // 데이터 로드
    loadChartData(stockCode).then(data => {
      candlestickSeries.setData(data);
    });
    
    // 클린업
    return () => {
      chart.remove();
    };
  }, [stockCode]);
  
  return <div ref={chartContainerRef} />;
}
```

---

## 📱 Phase 5: 반응형 디자인

### 5-1. Tailwind CSS 설치 (선택)

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### `tailwind.config.js` 설정
```javascript
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [],
}
```

#### `src/index.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 5-2. 반응형 레이아웃

#### 반응형 컴포넌트 예시
```javascript
function App() {
  return (
    <div className="flex flex-col md:flex-row h-screen">
      {/* 사이드바 - 모바일에서는 숨김 */}
      <aside className="
        hidden md:block
        w-64 bg-white shadow-lg
      ">
        <StockList />
      </aside>
      
      {/* 메인 차트 */}
      <main className="
        flex-1 p-4
        md:p-8
      ">
        <StockChart />
      </main>
    </div>
  );
}
```

#### 모바일 메뉴
```javascript
function MobileMenu() {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      {/* 햄버거 버튼 - 모바일만 */}
      <button
        className="md:hidden fixed top-4 left-4 z-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        ☰
      </button>
      
      {/* 슬라이드 메뉴 */}
      <div className={`
        fixed inset-y-0 left-0 w-64 bg-white shadow-lg
        transform transition-transform duration-300 z-40
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:hidden
      `}>
        <StockList />
      </div>
      
      {/* 오버레이 */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
```

### 5-3. 터치 제스처

#### 차트 핀치 줌 활성화
```javascript
const chart = createChart(chartContainerRef.current, {
  // ... 기존 설정
  handleScroll: {
    mouseWheel: !isMobile,
    pressedMouseMove: true,
    horzTouchDrag: true,
    vertTouchDrag: true,
  },
  handleScale: {
    mouseWheel: !isMobile,
    pinch: isMobile,
  },
});
```

---

## 🚀 Phase 6: 배포

### 6-1. 프로덕션 빌드

```bash
# React 앱 빌드
npm run build

# 빌드 결과물 확인
ls -la build/
```

### 6-2. Firebase Hosting 배포

#### `firebase.json` 설정 확인
```json
{
  "hosting": {
    "public": "build",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

#### 배포 실행
```bash
# Hosting만 배포
firebase deploy --only hosting

# 또는 전체 배포
firebase deploy
```

#### 배포 URL 확인
```
✔  Deploy complete!

Hosting URL: https://your-project.web.app
```

### 6-3. 커스텀 도메인 (선택)

1. Firebase Console → Hosting → 도메인 추가
2. 도메인 입력 (예: `stocks.yourdomain.com`)
3. DNS 레코드 추가:
   ```
   Type: A
   Name: stocks
   Value: [Firebase IP]
   ```
4. SSL 인증서 자동 생성 (몇 시간 소요)

---

## 🤖 Phase 7: Android 웹뷰 (선택)

### 7-1. Android Studio 프로젝트 생성

1. Android Studio 실행
2. "New Project" → "Empty Activity"
3. 프로젝트 이름: `StockChartApp`
4. 언어: Kotlin
5. Minimum SDK: API 24

### 7-2. WebView 구현

#### `AndroidManifest.xml` - 인터넷 권한 추가
```xml
<uses-permission android:name="android.permission.INTERNET" />
```

#### `activity_main.xml` - 레이아웃
```xml
<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</RelativeLayout>
```

#### `MainActivity.kt` - WebView 설정
간단한 구조만 제시 (코드는 생략 요청에 따라 최소화)

### 7-3. APK 빌드 및 배포

```bash
# Build → Generate Signed Bundle / APK
# APK 선택 → Next
# Create new key store (처음) 또는 Choose existing
# APK 생성 완료

# APK 파일 위치: app/release/app-release.apk
```

---

## 🔍 디버깅 및 모니터링

### Firebase Console에서 모니터링
1. **Firestore**: 데이터 확인
2. **Functions**: 실행 로그, 에러 확인
3. **Hosting**: 트래픽, 대역폭
4. **Performance**: 웹 성능 모니터링

### 로컬 디버깅
```bash
# React 개발 서버
npm start

# Firebase Emulator
firebase emulators:start

# Cloud Function 로그
firebase functions:log
```

---

## 📋 체크리스트 요약

### 필수 완료 항목
- [ ] Firebase 프로젝트 생성
- [ ] 데이터 마이그레이션 완료
- [ ] Cloud Function 작동 확인
- [ ] React 앱 Firestore 연동
- [ ] 반응형 디자인 적용
- [ ] Firebase Hosting 배포

### 선택 항목
- [ ] Tailwind CSS 적용
- [ ] 실시간 업데이트 구현
- [ ] Android 웹뷰 앱
- [ ] 커스텀 도메인
- [ ] Firebase Authentication

---

**다음 단계**: [비용 분석](COST_ANALYSIS.md)
