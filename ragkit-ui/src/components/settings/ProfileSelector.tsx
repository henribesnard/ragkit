import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RAG_PROFILES, RagProfile } from '@/data/profiles';
import { cn } from '@/utils/cn';

interface ProfileSelectorProps {
  selectedId?: string | null;
  onSelect: (profile: RagProfile) => void;
}

export function ProfileSelector({ selectedId, onSelect }: ProfileSelectorProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xl font-display">Recommended profiles</h3>
        <p className="text-sm text-muted">
          Pick a starting point. You can refine settings later in intermediate or expert mode.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {RAG_PROFILES.map((profile) => (
          <Card
            key={profile.id}
            className={cn(
              'group flex h-full flex-col border border-white/60 transition',
              selectedId === profile.id ? 'ring-2 ring-accent' : 'hover:-translate-y-1 hover:shadow-glow',
            )}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-muted">{profile.tag}</p>
                <h4 className="mt-2 text-lg font-display">{profile.name}</h4>
                <p className="mt-2 text-sm text-muted">{profile.description}</p>
              </div>
              {selectedId === profile.id ? (
                <span className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-white">
                  Selected
                </span>
              ) : null}
            </div>
            <div className="mt-auto pt-6">
              <Button variant={selectedId === profile.id ? 'primary' : 'outline'} onClick={() => onSelect(profile)}>
                Apply profile
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
