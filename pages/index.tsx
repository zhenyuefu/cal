import {useForm} from "@mantine/form";
import {ActionIcon, Box, Button, Center, Code, CopyButton, Group, Select, Text, Tooltip} from "@mantine/core";
import {randomId} from "@mantine/hooks";
import {IconCalendarEvent, IconCheck, IconCopy, IconTrash} from "@tabler/icons-react";
import Link from "next/link";


import fs from "fs";
import path from "path";
import type { GetStaticProps } from "next";

type Option = { label: string; value: string };
type Props = {
  optionsS1: Option[];
  optionsS2: Option[];
  optionsS3: Option[];
  groupCounts: Record<string, number>;
};

export default function IndexPage({ optionsS1, optionsS2, optionsS3, groupCounts }: Props) {
    const params = new URLSearchParams();


    const form = useForm({
        initialValues: {
            SEMESTER: "s2",
            UE: [{name: "", group: "1", key: randomId()}],
            MAJ: ""
        },
    });

    const semesters = [{label: "Semestre 1", value: ""}, {label: "Semestre 2", value: "s2"}, {label: "Semestre 3", value: "s3"}];


    // 动态生成的 UE 列表与组数，由 getStaticProps 提供
    const ue_s1 = optionsS1;
    const ue_s2 = optionsS2;
    const ue_s3 = optionsS3;

    const parcours = [
        {value: "AND", label: "AND"},
        {value: "SAR", label: "SAR"},
        {value: "STL", label: "STL"},
        {value: "DAC", label: "DAC"},
        {value: "DAS", label: "DAS"},
        {value: "BIM", label: "BIM"},
        {value: "IMA", label: "IMA"},
        {value: "SESI", label: "SESI"},
        {value: "SFPN", label: "SFPN"},
    ]

    form.values.MAJ ? params.set("MAJ", form.values.MAJ) : null;
    form.values.UE.forEach((ue, index) => {
        if (ue.name !== "" && ue.group) {
            // 直接使用裁剪后的代码/特殊键作为后端键
            params.set(ue.name, String(ue.group));
        }
    });
    const cal_url = `webcal://cal.fuzy.tech/api/gen` + form.getInputProps("SEMESTER").value + `?` + params.toString();
    const fields = form.values.UE.map((item, index) => (
        <Group key={item.key} mt="xs">
            <Select
                placeholder="UE"
                data={form.getInputProps("SEMESTER").value === "s2" ? ue_s2 : form.getInputProps("SEMESTER").value === "s3" ? ue_s3 : ue_s1}
                style={{flex: 1}}
                {...form.getInputProps(`UE.${index}.name`)}
            />
            <Select
                placeholder="Group"
                data={form.getInputProps(`UE.${index}.name`).value ? createGroups(
                        form.getInputProps(`UE.${index}.name`).value in groupCounts ? groupCounts[form.getInputProps(`UE.${index}.name`).value] : 1)
                    : createGroups(1)}
                style={{flex: 1}}
                {...form.getInputProps(`UE.${index}.group`)}
            />
            <ActionIcon
                color="red"
                onClick={() => form.removeListItem("UE", index)}
            >
                <IconTrash size={16}/>
            </ActionIcon>
        </Group>
    ));

    return (
        <Center>
            <Box style={{maxWidth: 500, margin: 20}} mx="auto">
                <Select placeholder="Semestre" data={semesters} {...form.getInputProps("SEMESTER")}/>
                <Select data={parcours} placeholder="Parcours" {...form.getInputProps("MAJ")}
                        style={{marginBottom: 20}}/>
                {fields.length > 0 ? (
                    <Group mb="xs">
                        <Text size="sm" fw={500} style={{flex: 1}}>
                            UE
                        </Text>
                        <Text size="sm" fw={500} style={{flex: 1}}>
                            Group
                        </Text>

                    </Group>
                ) : (
                    <Text c="dimmed" ta="center">
                        No UE here...
                    </Text>
                )}

                {fields}

                <Group justify="center" mt="md">
                    <Button
                        onClick={() =>
                            form.insertListItem("UE", {
                                name: "",
                                group: "1",
                                key: randomId(),
                            })
                        }
                    >
                        Add UE
                    </Button>
                </Group>

                <Text size="sm" fw={500} mt="md" style={{marginBottom: 10}}>
                    For your subscription link, please copy it and add it to your calendar:
                </Text>

                <div style={{display: "flex", float: "right", position: "relative", alignSelf: "right", top: 5}}>

                    <Link href={cal_url} legacyBehavior>
                        <a>
                            <ActionIcon>
                                <IconCalendarEvent size={16}/>
                            </ActionIcon>
                        </a>
                    </Link>

                    <CopyButton value={cal_url} timeout={2000}>
                        {({copied, copy}) => (
                            <Tooltip label={copied ? 'Copied' : 'Copy'} withArrow position="right">
                                <ActionIcon color={copied ? 'teal' : 'gray'} onClick={copy}>
                                    {copied ? <IconCheck size={16}/> : <IconCopy size={16}/>}
                                </ActionIcon>
                            </Tooltip>
                        )}
                    </CopyButton>
                </div>

                <Code block style={{marginBottom: 10}}>{cal_url}</Code>

                <Text component="div" style={{display: "flex", flexDirection: "column", gap: 6}}>
                  <a href="https://support.apple.com/guide/iphone/iph3d1110d4/ios" target="_blank" rel="noreferrer" style={{textDecoration: 'underline'}}>ios subscription instructions</a>
                  <a href="https://support.google.com/calendar/answer/37100" target="_blank" rel="noreferrer" style={{textDecoration: 'underline'}}>google calendar subscription instructions</a>
                  <a href="https://github.com/zhenyuefu/cal" target="_blank" rel="noreferrer" style={{textDecoration: 'underline'}}>github source code</a>
                </Text>
            </Box>
        </Center>
    )
        ;
}

function createGroups(n: number) {
    return Array.from({length: n}, (_, i) => ({
        value: String(i + 1),
        label: `Group ${i + 1}`,
    }));
}

// 从 ICS 与 Python 映射中生成动态的 UE 列表与组数
export const getStaticProps: GetStaticProps<Props> = async () => {
  const catalogPath = path.join(process.cwd(), "data", "courses.json");
  const raw = fs.readFileSync(catalogPath, "utf-8");
  const catalog = JSON.parse(raw) as {
    s1: Record<string, { label: string; parcours: string; groups: number }>;
    s2: Record<string, { label: string; parcours: string; groups: number }>;
    s3: Record<string, { label: string; parcours: string; groups: number }>;
  };

  const toOptions = (entries: Record<string, { label: string }>): Option[] =>
    Object.entries(entries)
      .map(([code, info]) => ({ value: code, label: info.label || code }))
      .sort((a, b) => a.label.localeCompare(b.label));

  const optionsS1 = toOptions(catalog.s1);
  const optionsS2 = toOptions(catalog.s2);
  const optionsS3 = toOptions(catalog.s3);

  const groupCounts: Record<string, number> = {};
  for (const [code, info] of Object.entries(catalog.s1)) groupCounts[code] = info.groups || 1;
  for (const [code, info] of Object.entries(catalog.s2)) groupCounts[code] = info.groups || 1;
  for (const [code, info] of Object.entries(catalog.s3)) groupCounts[code] = info.groups || 1;

  return { props: { optionsS1, optionsS2, optionsS3, groupCounts } };
};
