import type { Tag, Tool } from '~/lib/types';
import MultiSelect from '~/components/common/MultiSelect';

interface FilterBarProps {
    tags: Tag[];
    tools: Tool[];
    selectedTagIds: number[];
    selectedToolIds: number[];
    onChange: (selected: { tagIds: number[]; toolIds: number[] }) => void;
}

export default function FilterBar({
    tags,
    tools,
    selectedTagIds,
    selectedToolIds,
    onChange,
}: FilterBarProps) {
    const handleTagsChange = (newTagIds: number[]) => {
        onChange({ tagIds: newTagIds, toolIds: selectedToolIds });
    };

    const handleToolsChange = (newToolIds: number[]) => {
        onChange({ tagIds: selectedTagIds, toolIds: newToolIds });
    };

    return (
        <div className="flex items-center gap-2">
            <MultiSelect
                label="Tags"
                icon="sell"
                placeholder="Search tags..."
                items={tags}
                selectedIds={selectedTagIds}
                onChange={handleTagsChange}
                color="primary"
            />
            <MultiSelect
                label="Tools"
                icon="build"
                placeholder="Search tools..."
                items={tools}
                selectedIds={selectedToolIds}
                onChange={handleToolsChange}
                color="purple"
            />
        </div>
    );
}


