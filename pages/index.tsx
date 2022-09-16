import {useForm} from "@mantine/form";
import {
    Group,
    ActionIcon,
    Box,
    Text,
    Button,
    Code, Select, CopyButton, Tooltip,
} from "@mantine/core";
import {randomId} from "@mantine/hooks";
import {IconCheck, IconCopy, IconTrash, IconCalendarEvent} from "@tabler/icons";
import {NextLink} from "@mantine/next";


export default function IndexPage() {
    const params = new URLSearchParams();


    const form = useForm({
        initialValues: {
            UE: [{name: "", group: 0, key: randomId()}],
            MAJ: ""
        },
    });

    const groups = [
        {value: '1', label: 'GR1'},
        {value: '2', label: 'GR2'},
        {value: '3', label: 'GR3'},
        {value: '4', label: 'GR4'},
        {value: '5', label: 'GR5'},
    ];

    const all_ue = [
        {value: "MOGPL", label: "MOGPL"},
        {value: "IL", label: "IL"},
        {value: "LRC", label: "LRC"},
        {value: "MLBDA", label: "MLBDA"},
        {value: "MAPSI", label: "MAPSI"},
        {value: "AAGB", label: "AAGB"},
        {value: "Maths", label: "Maths"},
        {value: "BIMA", label: "BIMA"},
        {value: "PSCR", label: "PSCR"},
        {value: "NOYAU", label: "NOYAU"},
        {value: "MOBJ", label: "MOBJ"},
        {value: "ESA", label: "ESA"},
        {value: "ARCHI", label: "ARCHI"},
        {value: "SIGNAL", label: "SIGNAL"},
        {value: "VLSI", label: "VLSI"},
        {value: "SC", label: "SC"},
        {value: "PPAR", label: "PPAR"},
        {value: "COMPLEX", label: "COMPLEX"},
        {value: "MODEL", label: "MODEL"},
        {value: "ALGAV", label: "ALGAV"},
        {value: "DLP", label: "DLP"},
        {value: "OUV", label: "OUV"},
    ]

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
        if (ue.name !== "" && ue.group !== 0) {
            params.set(ue.name, ue.group.toString());
        }
    });
    const cal_url = `webcal://cal.fuzy.tech/api/gen?` + params.toString();
    const fields = form.values.UE.map((item, index) => (
        <Group key={item.key} mt="xs">
            <Select
                placeholder="UE"
                data={all_ue}
                sx={{display:"flex",flex: 1}}
                {...form.getInputProps(`UE.${index}.name`)}
            />
            <Select
                placeholder="Group"
                data={groups}
                sx={{display:"flex" ,flex: 1}}
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
        <Box sx={{maxWidth: 500}} mx="auto" style={{margin:20}}>
            <Select data={parcours} placeholder="你的专业" {...form.getInputProps("MAJ")}
                    sx={{marginBottom:20}}/>
            {fields.length > 0 ? (
                <Group mb="xs">
                    <Text size="sm" weight={500} sx={{flex: 1}}>
                        UE
                    </Text>
                    <Text size="sm" weight={500} sx={{flex: 1}}>
                        Group
                    </Text>

                </Group>
            ) : (
                <Text color="dimmed" align="center">
                    No UE here...
                </Text>
            )}

            {fields}

            <Group position="center" mt="md">
                <Button
                    onClick={() =>
                        form.insertListItem("UE", {
                            name: "",
                            group: 0,
                            key: randomId(),
                        })
                    }
                >
                    Add UE
                </Button>
            </Group>

            <Text size="sm" weight={500} mt="md" sx={{marginBottom: 10}}>
                你的订阅链接，请复制后添加到日历中:
            </Text>

            <div style={{display: "flex", float: "right", position: "relative", alignSelf: "right", top: 5}}>

                <NextLink href={cal_url}>
                    <ActionIcon>
                        <IconCalendarEvent size={16}/>
                    </ActionIcon>
                </NextLink>

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

            <Text variant="link" component="a" href="https://support.apple.com/zh-cn/HT202361"
                  sx={{display: "flex"}}>ios订阅说明</Text>
            <Text variant="link" component="a" href="https://support.google.com/calendar/answer/37100?hl=zh-Hans"
                  sx={{display: "flex"}}>Google日历订阅说明</Text>
        </Box>
    )
        ;
}
