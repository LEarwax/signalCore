// Public share page — no auth required
// Fetches snapshot from /api/share/:token

export default async function SharePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold mb-4">Shared Packet</h1>
      <p className="text-gray-500">Token: {token}</p>
      {/* TODO: fetch snapshot_data and render packet summary */}
    </div>
  );
}
