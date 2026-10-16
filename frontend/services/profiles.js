// Profile personalization is metadata only. It never alters the anatomical map.
export async function ensureProfile(client, userId) {
  if (!userId) throw new Error('Authentication required');
  const { error } = await client.from('profiles').upsert({ id: userId }, { onConflict: 'id', ignoreDuplicates: true });
  if (error) throw new Error('Profile unavailable');
}

export async function getProfile(client, userId) {
  if (!userId) throw new Error('Authentication required');
  const { data, error } = await client.from('profiles').select('id,display_name,preferred_language,height_cm,weight_kg').eq('id', userId).maybeSingle();
  if (error) throw new Error('Profile unavailable');
  return data;
}
