import { RoleAuthForm } from "@/components/auth/role-auth-form";

export default function ClinicianAuthPage() {
  return (
    <RoleAuthForm
      role="clinician"
      title="Clinician Sign In"
      subtitle="Sign in to access your pre-session briefs."
      destination="/clinician"
    />
  );
}
