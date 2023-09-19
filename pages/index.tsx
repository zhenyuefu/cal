import {useForm} from "@mantine/form";
import {ActionIcon, Box, Button, Center, Code, CopyButton, Group, Select, Text, Tooltip} from "@mantine/core";
import {randomId} from "@mantine/hooks";
import {IconCalendarEvent, IconCheck, IconCopy, IconTrash} from "@tabler/icons";
import {NextLink} from "@mantine/next";


export default function IndexPage() {
    const params = new URLSearchParams();


    const form = useForm({
        initialValues: {
            SEMESTER: "s2",
            UE: [{name: "", group: 1, key: randomId()}],
            MAJ: ""
        },
    });

    const semesters = [{label: "Semestre 1", value: ""}, {label: "Semestre 2", value: "s2"}, {label: "Semestre 3", value: "s3"}];


    // 存储每个UE的组的数量
    const groupCount = {
        "RA": 2,
        "MU4IN811": 2,
        "IAMSI": 2,
        "MOGPL": 4,
        "MLBDA": 3,
        "LRC": 5,
        "MAPSI": 5,
        "BIMA": 2,
        "COMPLEX": 2,
        "IL": 3,
        "DLP": 2,
        "ALGAV": 2,
        "MU5IN259": 2,
        "MU5IN862": 2,
        "MU5IN861": 3,
    };

    const ue_s1 = [
        {value: "MOGPL", label: "MOGPL"},
        {value: "IL", label: "IL"},
        {value: "LRC", label: "LRC"},
        {value: "MLBDA", label: "MLBDA"},
        {value: "MAPSI", label: "MAPSI"},
        {value: "BIMA", label: "BIMA"},
        {value: "COMPLEX", label: "COMPLEX"},
        {value: "MODEL", label: "MODEL"},
        {value: "PPAR", label: "PPAR"},
        {value: "ALGAV", label: "ALGAV"},
        {value: "DLP", label: "DLP"},
        {value: "OUV", label: "OUV"},
    ]

    const ue_s2 = [
        {value: "DJ", label: "DJ"},
        {value: "MU4IN202", label: "FoSyMa"},
        {value: "IHM", label: "IHM"},
        {value: "RA", label: "RA"},
        {value: "RP", label: "RP"},
        {value: "RITAL", label: "RITAL"},
        {value: "MU4IN811", label: "ML"},
        {value: "MU4IN812", label: "MLL"},
        {value: "IAMSI", label: "IAMSI"},
        {value: "SAM", label: "SAM"},
        {value: "IG3D", label: "IG3D"},
        {value: "MU4IN910", label: "ANUM"},
    ]

    const ue_s3 = [
        {value: "MU5IN250", label: "COCOMA"},
        {value: "MU5IN254", label: "MOSIMA"},
        {value: "MU5IN258", label: "ISG"},
        {value: "MU5IN256", label: "MADMC"},
        {value: "MU5IN257", label: "AOTJ"},
        {value: "MU5IN251", label: "MAOA"},
        {value: "MU5IN252", label: "EVHI"},
        {value: "MU5IN259", label: "IAR"},
        {value: "MU5IN852", label: "BDLE"},
        {value: "MU5IN860", label: "LODAS"},
        {value: "MU5IN861", label: "AMAL"},
        {value: "MU5IN862", label: "RLD"},
        {value: "MU5IN863", label: "REDS"},
        {value: "XAI", label: "XAI"},
        {value: "OIP", label: "OIP"}
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
    const cal_url = `webcal://cal.fuzy.tech/api/gen` + form.getInputProps("SEMESTER").value + `?` + params.toString();
    const fields = form.values.UE.map((item, index) => (
        <Group key={item.key} mt="xs">
            <Select
                placeholder="UE"
                data={form.getInputProps("SEMESTER").value === "s2" ? ue_s2 : form.getInputProps("SEMESTER").value === "s3" ? ue_s3 : ue_s1}
                sx={{flex: 1}}
                {...form.getInputProps(`UE.${index}.name`)}
            />
            <Select
                placeholder="Group"
                data={form.getInputProps(`UE.${index}.name`).value ? createGroups(
                        // @ts-ignore
                        form.getInputProps(`UE.${index}.name`).value in groupCount ? groupCount[form.getInputProps(`UE.${index}.name`).value] : 1)
                    : createGroups(1)}
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
        <Center>
            <Box sx={{maxWidth: 500}} mx="auto" style={{margin: 20}}>
                <Select placeholder="Semestre" data={semesters} {...form.getInputProps("SEMESTER")}/>
                <Select data={parcours} placeholder="Parcours" {...form.getInputProps("MAJ")}
                        sx={{marginBottom: 20}}/>
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
                                group: 1,
                                key: randomId(),
                            })
                        }
                    >
                        Add UE
                    </Button>
                </Group>

                <Text size="sm" weight={500} mt="md" sx={{marginBottom: 10}}>
                    For your subscription link, please copy it and add it to your calendar:
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

                <Text variant="link" component="a" href="https://support.apple.com/guide/iphone/iph3d1110d4/ios"
                      sx={{display: "flex"}}>ios subscription instructions</Text>
                <Text variant="link" component="a" href="https://support.google.com/calendar/answer/37100"
                      sx={{display: "flex"}}>google calendar subscription instructions</Text>
                <Text variant="link" component="a" href="https://github.com/zhenyuefu/cal"
                      sx={{display: "flex"}}>github source code</Text>
            </Box>
        </Center>
    )
        ;
}

function createGroups(n: number) {
    return Array.from({length: n}, (_, i) => ({
        value: i + 1,
        label: `Group ${i + 1}`,
    }));
}