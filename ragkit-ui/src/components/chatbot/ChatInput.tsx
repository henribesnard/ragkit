import { FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const { t } = useTranslation();
  const [value, setValue] = useState('');

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!value.trim()) return;
    onSend(value.trim());
    setValue('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <Input
        placeholder={t('chat.placeholder')}
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
      <Button type="submit" disabled={isLoading}>
        {isLoading ? '...' : t('chat.send')}
      </Button>
    </form>
  );
}
