# 주식 차트 앱 재구성 프로젝트

## 📌 프로젝트 개요

주식 차트 시각화 애플리케이션을 Spring Boot + FastAPI + MariaDB 구조에서 Firebase 기반 서버리스 아키텍처로 전환하는 프로젝트입니다.

## 🎯 프로젝트 목표

1. **서버 유지보수 부담 제거**: 서버리스 아키텍처로 전환
2. **디바이스 독립성**: 꺼져 있어도 자동으로 데이터 수집
3. **크로스 플랫폼 지원**: Desktop + Mobile (Android) 지원
4. **무료 운영**: Firebase Spark Plan 활용
5. **간소화**: 단일 코드베이스로 모든 플랫폼 커버

## 👥 사용자

- **사용자 수**: 2명 (개인 사용)
- **주요 사용**: Desktop (메인), Mobile (보조)

## 🔧 기술 스택

### 기존 시스템
- Frontend: React (CRA) + TradingView Lightweight Charts v5
- Backend: Spring Boot + FastAPI + MariaDB
- Data: 0.43MB
- Schedule: FastAPI schedule (매일 15:40)

### 새로운 시스템
- Frontend: React (CRA) + TradingView Lightweight Charts v5 (유지)
- Backend: Firebase Cloud Functions (Python/Node.js)
- Database: Firebase Firestore (월별 청크 구조)
- Authentication: Firebase Authentication (Google 로그인)
- Hosting: Firebase Hosting
- Mobile: Android WebView (선택사항)

## 📂 문서 구조

```
project-docs/
├── README.md                    # 이 파일 - 프로젝트 개요
├── CURRENT_SYSTEM.md           # 현재 시스템 상세 분석
├── ARCHITECTURE.md             # 새로운 아키텍처 설계
├── DATA_STRUCTURE.md           # Firestore 데이터 구조
├── MIGRATION_PLAN.md           # 마이그레이션 계획 및 로드맵
├── IMPLEMENTATION_GUIDE.md     # 단계별 구현 가이드
└── COST_ANALYSIS.md            # Firebase 비용 분석
```

## 🚀 빠른 시작

1. [현재 시스템 분석](CURRENT_SYSTEM.md) - 기존 시스템 이해
2. [새로운 아키텍처](ARCHITECTURE.md) - 목표 시스템 구조
3. [마이그레이션 계획](MIGRATION_PLAN.md) - 전환 로드맵
4. [구현 가이드](IMPLEMENTATION_GUIDE.md) - 실제 구현 단계

## ✅ 핵심 장점

- ✨ **무료 운영**: Firebase Spark Plan으로 영구 무료
- 🔄 **자동 실행**: Cloud Functions로 항상 동작
- 📱 **반응형**: 하나의 코드로 Desktop + Mobile
- 🚀 **빠른 배포**: 웹 배포 시 모든 기기 즉시 반영
- 🛠️ **간단 관리**: 서버 관리 불필요
- 🔐 **보안**: 구글 로그인으로 사용자별 데이터 분리
- ⚡ **고효율**: 월별 청크 구조로 읽기 95% 감소

## 📝 프로젝트 상태

- [x] 요구사항 분석 완료
- [x] 아키텍처 설계 완료
- [x] 문서화 완료
- [ ] Firebase 프로젝트 생성
- [ ] 데이터 마이그레이션
- [ ] Cloud Function 개발
- [ ] React 앱 수정
- [ ] 배포 및 테스트
- [ ] Android 웹뷰 앱 (선택)

## 🔗 참고 링크

- [Firebase 공식 문서](https://firebase.google.com/docs)
- [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/)
- [Create React App](https://create-react-app.dev/)

## 📞 문의

프로젝트 진행 중 질문사항이 있으면 각 문서를 참고하거나 이슈를 생성하세요.

---

**최종 업데이트**: 2025-11-04
