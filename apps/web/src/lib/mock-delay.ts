export function mockDelay(ms = 280): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
