import EssayDetailClient from './EssayDetailClient';

export const runtime = 'edge';

interface EssayDetailPageProps {
  params: {
    id: string;
  };
}

export default function EssayDetailPage({ params }: EssayDetailPageProps) {
  return <EssayDetailClient essayId={params.id} />;
}
