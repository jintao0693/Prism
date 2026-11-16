import { redirect } from "next/navigation";
import { ApiError } from "@/lib/api-client";
import { routes } from "@/lib/routes";

/** RSC 调后端失败时：未登录跳登录页，其它错误继续抛出。 */
export function redirectIfUnauthorized(err: unknown): never {
  if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
    redirect(routes.login);
  }
  throw err;
}

export async function withAuthRedirect<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err) {
    redirectIfUnauthorized(err);
  }
}
