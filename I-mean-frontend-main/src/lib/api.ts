const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchSomething() {
  const res = await fetch(`${API_URL}/your-endpoint`);
  return res.json();
}
