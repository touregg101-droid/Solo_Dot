import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata={title:'SOLO DOT · 혼자여도, 어딘가 함께',description:'같은 도시, 각자의 여행. 정확한 위치 없이 작은 점으로 안부를 전하는 여행 앱 시안.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="ko"><body>{children}</body></html>}
