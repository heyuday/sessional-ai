import { RoleAuthForm } from "@/components/auth/role-auth-form";

export default function PatientAuthPage() {
  return (
    <RoleAuthForm
      role="patient"
      title="Patient Sign In"
      subtitle="Sign in to continue your voice check-ins."
      destination="/patient"
    />
  );
}
