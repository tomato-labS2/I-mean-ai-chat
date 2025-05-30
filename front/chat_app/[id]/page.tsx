import ChatPageClient from "@/features/chat/components/ChatPageClient"

export function generateStaticParams(): Array<{ id: string }> {
  return [
    { id: 'general' }, // '일반' 채팅방
    { id: 'support' }, // '고객 지원' 채팅방
    { id: 'feedback' }, // '피드백' 채팅방
  ];
}

export default async function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  const roomId = resolvedParams.id;

  return <ChatPageClient roomId={roomId} />;
}
