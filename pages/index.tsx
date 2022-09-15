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
import {IconCheck, IconCopy, IconTrash} from "@tabler/icons";


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

    form.values.MAJ? params.set("MAJ", form.values.MAJ): null;
    form.values.UE.forEach((ue, index) => {
        if (ue.name !== "" && ue.group !== 0) {
            params.set(ue.name, ue.group.toString());
        }
    });
    const cal_url = `https://cal.fuzy.tech/api/gen?` + params.toString();
    const fields = form.values.UE.map((item, index) => (
        <Group key={item.key} mt="xs">
            <Select
                placeholder="UE"
                data={all_ue}
                sx={{flex: 1}}
                {...form.getInputProps(`UE.${index}.name`)}
            />
            <Select
                placeholder="Group"
                data={groups}
                sx={{flex: 1}}
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
        <Box sx={{maxWidth: 500}} mx="auto">
            <Select data={parcours} placeholder="你的专业" {...form.getInputProps("MAJ")}
                    sx={{margin: 45, marginLeft: 0}}/>
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

            <Text size="sm" weight={500} mt="md">
                Your Calender URL:
            </Text>

            <div style={{float:"right",position:"relative",alignSelf:"right",right:35,top:5}}>

            <CopyButton value={cal_url} timeout={2000} >
                {({copied, copy}) => (
                    <Tooltip label={copied ? 'Copied' : 'Copy'} withArrow position="right">
                        <ActionIcon color={copied ? 'teal' : 'gray'} onClick={copy}>
                            {copied ? <IconCheck size={16}/> : <IconCopy size={16}/>}
                        </ActionIcon>
                    </Tooltip>
                )}
            </CopyButton>
                </div>
             <Code block>{cal_url}</Code>

        </Box>
    )
        ;
}
