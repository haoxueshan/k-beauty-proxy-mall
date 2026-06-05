import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <div className="container pb-16">
      <AuthForm mode="login" />
    </div>
  );
}
