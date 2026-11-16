import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { routes } from "@/lib/routes";

export default async function RootPage() {
  const jar = await cookies();
  const token = jar.get("prism_access_token")?.value;
  redirect(token ? routes.workspaces : routes.login);
}
