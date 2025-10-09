import { redirect } from 'next/navigation';

export default function IeltsRegisterRedirect() {
  redirect('/auth?mode=register&redirect=/ielts/dashboard');
}
