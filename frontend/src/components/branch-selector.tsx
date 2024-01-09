import { useMutation } from "@apollo/client";
import { Icon } from "@iconify-icon/react";
import { format, formatDistanceToNow } from "date-fns";
import { useAtom } from "jotai";
import { useAtomValue } from "jotai/index";
import { useCallback, useContext, useState } from "react";
import { StringParam, useQueryParam } from "use-query-params";
import { QSP } from "../config/qsp";
import { AuthContext } from "../decorators/withAuth";
import { Branch } from "../generated/graphql";
import { BRANCH_CREATE } from "../graphql/mutations/branches/createBranch";
import { branchesState, currentBranchAtom } from "../state/atoms/branches.atom";
import { classNames } from "../utils/common";
import { BUTTON_TYPES, Button } from "./buttons/button";
import { SelectButton } from "./buttons/select-button";
import { POPOVER_SIZE, PopOver } from "./display/popover";
import { Input } from "./inputs/input";
import { Select, SelectOption } from "./inputs/select";
import { Switch } from "./inputs/switch";

export default function BranchSelector() {
  const [branches, setBranches] = useAtom(branchesState);
  const [, setBranchInQueryString] = useQueryParam(QSP.BRANCH, StringParam);
  const branch = useAtomValue(currentBranchAtom);
  const auth = useContext(AuthContext);

  const [newBranchName, setNewBranchName] = useState("");
  const [newBranchDescription, setNewBranchDescription] = useState("");
  const [originBranch, setOriginBranch] = useState();
  const [branchedFrom] = useState(); // TODO: Add calendar component
  const [isDataOnly, setIsDataOnly] = useState(true);

  const [createBranch, { loading }] = useMutation(BRANCH_CREATE);

  const valueLabel = (
    <>
      <Icon icon={"mdi:layers-triple"} />
      <p className="ml-2.5 text-sm font-medium">{branch?.name}</p>
    </>
  );

  const PopOverButton = (
    <Button
      disabled={!auth?.permissions?.write}
      buttonType={BUTTON_TYPES.MAIN}
      className="h-full rounded-r-md border border-transparent"
      type="submit"
      data-cy="create-branch-button"
      data-testid="create-branch-button">
      <Icon icon={"mdi:plus"} className="text-custom-white" />
    </Button>
  );

  const branchesOptions: SelectOption[] = branches
    .map((branch) => ({
      id: branch.id,
      name: branch.name,
      is_data_only: branch.is_data_only,
      is_default: branch.is_default,
      created_at: branch.created_at,
    }))
    .sort((branch1, branch2) => {
      if (branch1.name === "main") {
        return -1;
      }

      if (branch2.name === "main") {
        return 1;
      }

      if (branch2.name === "main") {
        return -1;
      }

      if (branch1.name > branch2.name) {
        return 1;
      }

      return -1;
    });

  const defaultBranch = branches?.filter((b) => b.is_default)[0]?.id;

  /**
   * Update GraphQL client endpoint whenever branch changes
   */
  const onBranchChange = useCallback((branch: Branch) => {
    if (branch?.is_default) {
      // undefined is needed to remove a parameter from the QSP
      setBranchInQueryString(undefined);
    } else {
      setBranchInQueryString(branch.name);
    }
  }, []);

  const handleBranchedFrom = (newBranch: any) => setOriginBranch(newBranch);

  const renderOption = ({ option, active, selected }: any) => (
    <div className="flex relative flex-col">
      {option.is_data_only && (
        <div className="absolute bottom-0 right-0">
          <Icon
            icon={"mdi:database"}
            className={classNames(active ? "text-custom-white" : "text-gray-500")}
          />
        </div>
      )}

      {option.is_default && (
        <div className="absolute bottom-0 right-0">
          <Icon
            icon={"mdi:shield-check"}
            className={classNames(active ? "text-custom-white" : "text-gray-500")}
          />
        </div>
      )}

      <div className="flex justify-between">
        <p className={selected ? "font-semibold" : "font-normal"}>{option.name}</p>
        {selected ? (
          <span className={active ? "text-custom-white" : "text-gray-500"}>
            <Icon icon={"mdi:check"} />
          </span>
        ) : null}
      </div>

      {option?.created_at && (
        <p className={classNames(active ? "text-custom-white" : "text-gray-500", "mt-2")}>
          {formatDistanceToNow(new Date(option?.created_at), {
            addSuffix: true,
          })}
        </p>
      )}
    </div>
  );

  const handleSubmit = async (close: any) => {
    try {
      const { data } = await createBranch({
        variables: {
          name: newBranchName,
          description: newBranchDescription,
          is_data_only: isDataOnly,
        },
      });

      const branchCreated = data?.BranchCreate?.object;
      if (branchCreated) {
        setBranches([...branches, branchCreated]);
        onBranchChange(branchCreated);
      }

      close();
    } catch (error) {
      console.error("Error while creating the branch: ", error);
    }
  };

  /**
   * There's always a main branch present at least.
   */
  if (!branches.length) {
    return null;
  }

  return (
    <div
      className="flex items-stretch"
      data-cy="branch-select-menu"
      data-testid="branch-select-menu">
      <SelectButton
        value={branch}
        valueLabel={valueLabel}
        onChange={onBranchChange}
        options={branchesOptions}
        renderOption={renderOption}
      />
      <PopOver
        disabled={!auth?.permissions?.write}
        buttonComponent={PopOverButton}
        className="right-0"
        title={"Create a new branch"}
        height={POPOVER_SIZE.NONE}>
        {({ close }: any) => (
          <>
            <div className="flex flex-col">
              <label htmlFor="new-branch-name">Branch name:</label>
              <Input id="new-branch-name" value={newBranchName} onChange={setNewBranchName} />
              <label htmlFor="new-branch-description">Branch description:</label>
              <Input
                id="new-branch-description"
                value={newBranchDescription}
                onChange={setNewBranchDescription}
              />
              Branched from:
              <Select
                disabled
                options={branchesOptions}
                value={originBranch ?? defaultBranch}
                onChange={handleBranchedFrom}
              />
              Branched at:
              <Input
                value={format(branchedFrom ?? new Date(), "MM/dd/yyy HH:mm")}
                onChange={setNewBranchName}
                disabled
              />
              Is data only:
              <Switch checked={isDataOnly} onChange={setIsDataOnly} />
            </div>

            <div className="flex justify-center">
              <Button
                isLoading={loading}
                buttonType={BUTTON_TYPES.VALIDATE}
                onClick={() => handleSubmit(close)}
                className="mt-2">
                Create
              </Button>
            </div>
          </>
        )}
      </PopOver>
    </div>
  );
}
