# Firebase 비용 분석

## 💰 Firebase 요금제

### Spark Plan (무료)
Firebase의 무료 요금제로, 소규모 프로젝트에 적합합니다.

### Blaze Plan (종량제)
사용한 만큼 지불하는 요금제이며, 무료 할당량도 포함되어 있습니다.

---

## 📊 Spark Plan 무료 할당량

### Firestore Database

| 항목 | 무료 할당량 | 단위 |
|------|-------------|------|
| **저장 용량** | 1 GB | 저장된 데이터 |
| **문서 읽기** | 50,000 / 일 | 읽기 작업 |
| **문서 쓰기** | 20,000 / 일 | 쓰기 작업 |
| **문서 삭제** | 20,000 / 일 | 삭제 작업 |

### Cloud Functions

| 항목 | 무료 할당량 | 단위 |
|------|-------------|------|
| **호출 횟수** | 2,000,000 / 월 | 함수 실행 |
| **GB-초** | 400,000 / 월 | 컴퓨팅 시간 |
| **CPU-초** | 200,000 / 월 | CPU 시간 |
| **아웃바운드 네트워킹** | 5 GB / 월 | 데이터 전송 |

### Cloud Scheduler

| 항목 | 무료 할당량 | 단위 |
|------|-------------|------|
| **작업 실행** | 3개 작업 | 무료 |

### Firebase Hosting

| 항목 | 무료 할당량 | 단위 |
|------|-------------|------|
| **저장 용량** | 10 GB | 호스팅 파일 |
| **전송량** | 360 MB / 일 | 다운로드 |

---

## 📈 프로젝트 예상 사용량 (2명 사용자)

### 데이터 저장 (Firestore)

#### 현재 데이터
```
MariaDB 현재 크기: 0.43 MB

Firestore 변환 후:
- stocks/{code}: 50종목 × 600 bytes = 30 KB
- daily 데이터: 현재 약 400 KB
- 사용자 데이터: 4 KB
- 메타데이터: 10 KB

총: 약 450 KB
```

#### 10년 후 예상
```
50종목 × 250일/년 × 10년 × 150 bytes = 18.75 MB

총 예상: ~20 MB
```

**결론**: ✅ 1 GB 할당량의 **2%** 사용

---

### 일일 쓰기 (Firestore)

#### Cloud Function 실행 (매일 15:40)
```
50종목 × 1일 데이터 = 50 writes
메타데이터 업데이트 = 1 write
배당 업데이트 (가끔) = 0~5 writes

총: ~55 writes/일
```

#### 사용자 활동
```
가로선 저장: 2명 × 5회 = 10 writes/일
설정 변경: 2명 × 2회 = 4 writes/일

총: ~14 writes/일
```

**일일 총 쓰기**: ~69 writes/일  
**할당량 대비**: 20,000의 **0.35%**

**결론**: ✅ 매우 여유로움

---

### 일일 읽기 (Firestore)

#### 사용자 1명당
```
앱 시작 (종목 리스트): 1 read
선택 종목 정보: 1 read
차트 데이터 (250일): 1 read (쿼리 1회로 가능)
배당 정보: 포함됨
가로선 로드: 1 read

종목 전환 시: 2 reads × 5회 = 10 reads
추가 탐색: ~10 reads

일일 총: ~25 reads
```

#### 2명 사용자
```
25 reads × 2명 = 50 reads/일
```

#### 로컬 캐싱 적용 시
```
초기 로드 후 캐싱 → 읽기 대폭 감소
증분 동기화만 → 10 reads/일

2명 총: ~20 reads/일
```

**할당량 대비**: 50,000의 **0.1%**

**결론**: ✅ 압도적으로 여유로움

---

### Cloud Functions

#### 월간 실행
```
매일 15:40 실행: 30회/월 (평일만이면 ~22회)
```

#### 실행당 사양
```
메모리: 256 MB
실행 시간: ~10초 (한투 API 호출 포함)
CPU 시간: ~10초
```

#### 월간 사용량
```
호출: 30회 / 2,000,000 = 0.0015%
GB-초: 30 × 10 × 0.25 = 75 GB-초 / 400,000 = 0.02%
CPU-초: 30 × 10 = 300 / 200,000 = 0.15%
```

**결론**: ✅ 무시할 수 있는 수준

---

### Firebase Hosting

#### 웹 앱 크기
```
React 빌드: ~2 MB (일반적)
압축 후: ~500 KB
```

#### 월간 트래픽
```
2명 사용자
앱 로드: 2명 × 10회/일 × 500 KB = 10 MB/일
월간: 10 MB × 30 = 300 MB/월

할당량: 10.8 GB/월 (360 MB/일 × 30일)
사용: 300 MB / 10,800 MB = 2.8%
```

**결론**: ✅ 충분

---

## 💵 Spark Plan 총 비용

### 월간 예상
```
Firestore:
  - 저장: 0.45 MB / 1 GB = 무료
  - 쓰기: 2,070 / 600,000 = 무료
  - 읽기: 1,500 / 1,500,000 = 무료

Cloud Functions:
  - 호출: 30 / 2,000,000 = 무료
  - GB-초: 75 / 400,000 = 무료
  - CPU-초: 300 / 200,000 = 무료

Hosting:
  - 저장: 2 MB / 10 GB = 무료
  - 전송: 300 MB / 10.8 GB = 무료

총 비용: $0/월
```

---

## 📊 사용량 시나리오별 비교

### 시나리오 1: 현재 계획 (2명)
| 리소스 | 사용량 | 할당량 대비 | 비용 |
|---------|---------|-------------|------|
| Firestore 읽기 | 1,500/월 | 0.1% | $0 |
| Firestore 쓰기 | 2,070/월 | 0.35% | $0 |
| Cloud Functions | 30회/월 | 0.0015% | $0 |
| **총 비용** | - | - | **$0** |

### 시나리오 2: 활성 사용 (2명, 매일 사용)
| 리소스 | 사용량 | 할당량 대비 | 비용 |
|---------|---------|-------------|------|
| Firestore 읽기 | 10,000/월 | 0.67% | $0 |
| Firestore 쓰기 | 3,000/월 | 0.5% | $0 |
| Cloud Functions | 30회/월 | 0.0015% | $0 |
| **총 비용** | - | - | **$0** |

### 시나리오 3: 사용자 증가 (10명)
| 리소스 | 사용량 | 할당량 대비 | 비용 |
|---------|---------|-------------|------|
| Firestore 읽기 | 50,000/월 | 3.3% | $0 |
| Firestore 쓰기 | 5,000/월 | 0.83% | $0 |
| Cloud Functions | 30회/월 | 0.0015% | $0 |
| **총 비용** | - | - | **$0** |

### 시나리오 4: 서비스 확장 (100명)
| 리소스 | 사용량 | 할당량 대비 | 비용 |
|---------|---------|-------------|------|
| Firestore 읽기 | 500,000/월 | 33% | $0 |
| Firestore 쓰기 | 20,000/월 | 3.3% | $0 |
| Cloud Functions | 30회/월 | 0.0015% | $0 |
| **총 비용** | - | - | **$0** |

> **참고**: 100명까지도 Spark Plan으로 충분할 것으로 예상됩니다!

---

## 🚨 할당량 초과 시 대응

### Spark Plan 한계점
- 일일 읽기 50,000 초과
- 일일 쓰기 20,000 초과
- 저장 1 GB 초과

### 대응 방안

#### 1단계: 최적화
```
읽기 최적화:
- 로컬 캐싱 강화
- IndexedDB 활용
- 증분 동기화만 사용

쓰기 최적화:
- 배치 쓰기 사용
- 불필요한 업데이트 제거
```

#### 2단계: Blaze Plan 전환
```
Blaze Plan 무료 할당량 (Spark와 동일):
- 읽기: 50,000/일 무료
- 쓰기: 20,000/일 무료
- 이후 종량제

초과 요금:
- 읽기: $0.06 / 10만 건
- 쓰기: $0.18 / 10만 건
- 삭제: $0.02 / 10만 건
```

#### 예시: 초과 시 비용
```
읽기 100,000/일 초과 시:
(100,000 - 50,000) / 100,000 × $0.06 = $0.03/일
월: $0.90

쓰기 30,000/일 초과 시:
(30,000 - 20,000) / 100,000 × $0.18 = $0.018/일
월: $0.54

총: ~$1.5/월
```

---

## 💡 비용 최적화 전략

### 1. 읽기 최적화

#### 로컬 캐싱
```javascript
// IndexedDB 또는 localStorage 활용
const cachedData = await getFromCache(stockCode);
if (cachedData && !isStale(cachedData)) {
  return cachedData; // Firestore 읽기 0회
}

// 필요시만 Firestore 조회
const freshData = await fetchFromFirestore(stockCode);
await saveToCache(stockCode, freshData);
return freshData;
```

#### 배치 읽기
```javascript
// ❌ 나쁜 예: N회 읽기
for (const code of codes) {
  await db.collection('stocks').doc(code).get(); // 50 reads
}

// ✅ 좋은 예: 1회 읽기
const query = db.collection('stocks').where('code', 'in', codes);
const snapshot = await query.get(); // 1 read
```

### 2. 쓰기 최적화

#### 배치 쓰기
```javascript
// ❌ 나쁜 예: 50회 쓰기
for (const data of dailyData) {
  await db.collection('stocks').doc(code).collection('daily')
    .doc(data.date).set(data); // 50 writes
}

// ✅ 좋은 예: 1회 배치
const batch = db.batch();
dailyData.forEach(data => {
  const ref = db.collection('stocks').doc(code)
    .collection('daily').doc(data.date);
  batch.set(ref, data);
});
await batch.commit(); // 50 writes (배치는 write 횟수는 같지만 네트워크 효율적)
```

#### 불필요한 업데이트 방지
```javascript
// 실제 변경 사항이 있을 때만 업데이트
if (hasChanges(oldData, newData)) {
  await updateFirestore(newData);
}
```

### 3. 저장 공간 최적화

#### 데이터 압축
```javascript
// 오래된 데이터 아카이빙 (필요시)
// 2년 이상 된 데이터를 Cloud Storage로 이동
```

#### 불필요한 필드 제거
```javascript
// 중복 데이터 제거
// 계산 가능한 데이터 제외
```

---

## 📱 모니터링 및 알림

### Firebase Console
1. **Usage and Billing** 탭에서 실시간 확인
2. 사용량 그래프 확인
3. 할당량 도달 예상 시간 확인

### 알림 설정
```
Firebase Console → Project Settings → Usage and billing
→ Set budget alerts

설정:
- 80% 도달 시: 이메일 알림
- 90% 도달 시: 이메일 + SMS
- 100% 도달 시: 긴급 알림
```

### 일일 체크 스크립트
```javascript
// 사용량 모니터링 Cloud Function (주간)
exports.checkUsage = functions.pubsub
  .schedule('0 9 * * 1') // 매주 월요일 9시
  .onRun(async (context) => {
    const usage = await getFirestoreUsage();
    
    if (usage.reads > 40000 || usage.writes > 15000) {
      await sendAlert('할당량 80% 초과');
    }
  });
```

---

## 🎯 비용 결론

### 2명 사용 시
```
✅ Spark Plan 영구 무료
✅ 할당량의 1% 미만 사용
✅ 추가 비용 0원
```

### 확장 시나리오
```
10명까지: Spark Plan 충분
100명까지: Spark Plan 가능 (최적화 필요)
100명 초과: Blaze Plan 전환 (월 $5~10 예상)
```

### 기존 시스템 대비
```
기존 (서버 운영):
- 서버 호스팅: 월 $10~50
- 전기료: 월 $5~10
- 유지보수 시간: 무형 비용

새 시스템 (Firebase):
- 호스팅: $0
- 전기료: $0
- 유지보수: 최소

절감 효과: 월 $15~60 + 시간 절약
```

---

## 📊 ROI (투자 대비 효과)

### 비용
```
개발 시간: ~30시간
시간당 가치: 가변적
월 운영비: $0

1년 총 비용: $0 (개발 시간 제외)
```

### 효과
```
서버 관리 불필요
자동화된 데이터 수집
디바이스 독립성
크로스 플랫폼 지원
무료 운영

연간 절감: $180~720 + 시간
```

---

## 🔮 장기 비용 예측

### 1년 후
```
데이터 증가: +2.5 MB
사용자: 2명 유지
비용: $0/월
```

### 5년 후
```
데이터 증가: +12.5 MB
사용자: 2~5명
비용: $0/월 (여전히 Spark Plan 충분)
```

### 10년 후
```
데이터 증가: +25 MB (총 ~30 MB)
사용자: 2~10명
비용: $0/월 (Spark Plan 충분)
```

---

**결론**: 현재 계획(2명 사용)으로는 **Firebase Spark Plan으로 영구 무료 운영이 가능**합니다! 🎉

---

**관련 문서**:
- [프로젝트 개요](README.md)
- [마이그레이션 계획](MIGRATION_PLAN.md)
- [구현 가이드](IMPLEMENTATION_GUIDE.md)
