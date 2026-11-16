"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import BrandMark from "@/components/ui/BrandMark";
import Button from "@/components/ui/Button";
import Panel from "@/components/ui/Panel";
import { loginWithPassword } from "@/features/auth";
import { routes } from "@/lib/routes";
import styles from "./login.module.css";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("linqing@prism.demo");
  const [password, setPassword] = useState("prism123");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(() => {
      void loginWithPassword(email, password)
        .then(() => router.push(routes.workspaces))
        .catch((err: Error) => setError(err.message || "登录失败"));
    });
  }

  return (
    <div className={styles.screen}>
      <Panel className={styles.card}>
        <BrandMark />
        <h1>登录 Prism</h1>
        <p>演示账号默认已填。登录后可在设置页配置火山方舟模型。</p>
        <form className={styles.form} onSubmit={onSubmit}>
          <label>
            邮箱
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label>
            密码
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error ? <p className={styles.error}>{error}</p> : null}
          <Button type="submit" className={styles.btn} disabled={pending}>
            {pending ? "登录中…" : "登录"}
          </Button>
        </form>
      </Panel>
    </div>
  );
}
