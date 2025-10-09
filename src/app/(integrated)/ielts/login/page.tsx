import { redirect } from 'next/navigation';

export default function IeltsLoginRedirect() {
  redirect('/auth?mode=login&redirect=/ielts/dashboard');
}
