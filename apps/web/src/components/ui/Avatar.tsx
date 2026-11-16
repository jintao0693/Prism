import styles from "./Avatar.module.css";

export interface AvatarProps {
  text: string;
}

export default function Avatar({ text }: AvatarProps) {
  return <div className={styles.avatar}>{text}</div>;
}
