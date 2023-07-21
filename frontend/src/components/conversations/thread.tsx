import { gql, useReactiveVar } from "@apollo/client";
import { TrashIcon } from "@heroicons/react/24/outline";
import { formatISO, isBefore, parseISO } from "date-fns";
import * as R from "ramda";
import { useContext, useState } from "react";
import { toast } from "react-toastify";
import {
  PROPOSED_CHANGES_CHANGE_THREAD_OBJECT,
  PROPOSED_CHANGES_THREAD_COMMENT_OBJECT,
} from "../../config/constants";
import { AuthContext } from "../../decorators/withAuth";
import graphqlClient from "../../graphql/graphqlClientApollo";
import { createObject } from "../../graphql/mutations/objects/createObject";
import { deleteObject } from "../../graphql/mutations/objects/deleteObject";
import { updateObjectWithId } from "../../graphql/mutations/objects/updateObjectWithId";
import { branchVar } from "../../graphql/variables/branchVar";
import { dateVar } from "../../graphql/variables/dateVar";
import { stringifyWithoutQuotes } from "../../utils/string";
import { ALERT_TYPES, Alert } from "../alert";
import { BUTTON_TYPES, Button } from "../button";
import { Checkbox } from "../checkbox";
import ModalConfirm from "../modal-confirm";
import ModalDelete from "../modal-delete";
import { AddComment } from "./add-comment";
import { Comment } from "./comment";

type tThread = {
  thread: any;
  refetch: Function;
};

// Sort by date desc
export const sortByDate = R.sort((a: any, b: any) =>
  isBefore(parseISO(a.created_at?.value || new Date()), parseISO(b.created_at?.value || new Date()))
    ? -1
    : 1
);

export const Thread = (props: tThread) => {
  const { thread, refetch } = props;

  const auth = useContext(AuthContext);

  const { comments } = thread;

  const branch = useReactiveVar(branchVar);
  const date = useReactiveVar(dateVar);
  const [isLoading, setIsLoading] = useState(false);
  const [displayAddComment, setDisplayAddComment] = useState(false);
  const [deleteModal, setDeleteModal] = useState(false);
  const [confirmModal, setConfirmModal] = useState(false);
  const [markAsResolved, setMarkAsResolved] = useState(false);

  const handleSubmit = async (data: any) => {
    try {
      if (!data) {
        return;
      }

      const newObject = {
        text: {
          value: data.comment,
        },
        thread: {
          id: thread.id,
        },
        created_by: {
          id: auth?.data?.sub,
        },
        created_at: {
          value: formatISO(new Date()),
        },
      };

      const mutationString = createObject({
        kind: PROPOSED_CHANGES_THREAD_COMMENT_OBJECT,
        data: stringifyWithoutQuotes(newObject),
      });

      const mutation = gql`
        ${mutationString}
      `;

      await graphqlClient.mutate({
        mutation,
        context: {
          branch: branch?.name,
          date,
        },
      });

      if (markAsResolved) {
        // If the resolved checkbox was checked, we need to resolve the thread after the comment
        await handleResolve();
      }

      toast(<Alert type={ALERT_TYPES.SUCCESS} message={"Comment added"} />);

      refetch();

      setIsLoading(false);
    } catch (error: any) {
      console.error("An error occured while creating the comment: ", error);

      toast(
        <Alert
          type={ALERT_TYPES.ERROR}
          message={"An error occured while creating the comment"}
          details={error.message}
        />
      );

      setIsLoading(false);
    }
  };

  const handleDeleteObject = async () => {
    if (!thread.id) {
      return;
    }

    setIsLoading(true);

    const mutationString = deleteObject({
      kind: PROPOSED_CHANGES_CHANGE_THREAD_OBJECT,
      data: stringifyWithoutQuotes({
        id: thread.id,
      }),
    });

    const mutation = gql`
      ${mutationString}
    `;

    await graphqlClient.mutate({
      mutation,
      context: { branch: branch?.name, date },
    });

    refetch();

    setDeleteModal(false);

    setIsLoading(false);

    toast(<Alert type={ALERT_TYPES.SUCCESS} message={"Thread deleted"} />);
  };

  const handleResolve = async () => {
    if (!thread.id) {
      return;
    }

    if (displayAddComment && !markAsResolved) {
      // If we want to resolve while submitting, we need to stop here and let the user submit the comment form
      setMarkAsResolved(true);
      setConfirmModal(false);
      return;
    }

    const mutationString = updateObjectWithId({
      kind: PROPOSED_CHANGES_CHANGE_THREAD_OBJECT,
      data: stringifyWithoutQuotes({
        id: thread.id,
        resolved: {
          value: true,
        },
      }),
    });

    const mutation = gql`
      ${mutationString}
    `;

    await graphqlClient.mutate({
      mutation,
      context: { branch: branch?.name, date },
    });

    refetch();

    if (confirmModal) {
      setConfirmModal(false);
    }

    if (displayAddComment) {
      setDisplayAddComment(false);
    }

    toast(<Alert type={ALERT_TYPES.SUCCESS} message={"Thread resolved"} />);
  };

  const sortedComments = sortByDate(comments.edges);

  const isResolved = thread?.resolved?.value;

  const MarkAsResolved = (
    <div className="flex items-center">
      <div className="mr-2">Resolved: </div>

      <Checkbox
        disabled={isResolved}
        enabled={isResolved || markAsResolved}
        onChange={() => setConfirmModal(true)}
      />
    </div>
  );

  return (
    <section className="bg-custom-white p-4 mb-4 rounded-lg relative group">
      <Button
        buttonType={BUTTON_TYPES.INVISIBLE}
        className="absolute -right-4 -top-4 hidden group-hover:block"
        onClick={() => setDeleteModal(true)}>
        <TrashIcon className="h-4 w-4 text-red-500" />
      </Button>

      <div className="">
        {sortedComments.map((comment: any, index: number) => (
          <Comment key={index} comment={comment.node} className={"border border-gray-200"} />
        ))}
      </div>

      <div className="flex">
        {displayAddComment && (
          <div className="flex-1">
            <AddComment
              onSubmit={handleSubmit}
              isLoading={isLoading}
              onClose={() => setDisplayAddComment(false)}
              disabled={!auth?.permissions?.write}
              additionalButtons={MarkAsResolved}
            />
          </div>
        )}

        {!displayAddComment && (
          <div className="flex flex-1 justify-between">
            {MarkAsResolved}

            <Button onClick={() => setDisplayAddComment(true)} disabled={!auth?.permissions?.write}>
              Reply
            </Button>
          </div>
        )}
      </div>

      <ModalDelete
        title="Delete"
        description={"Are you sure you want to remove this thread?"}
        onCancel={() => setDeleteModal(false)}
        onDelete={handleDeleteObject}
        open={!!deleteModal}
        setOpen={() => setDeleteModal(false)}
        isLoading={isLoading}
      />

      <ModalConfirm
        title="Confirm"
        description={"Are you sure you want to mark this thread as resolved?"}
        onCancel={() => setConfirmModal(false)}
        onConfirm={handleResolve}
        open={!!confirmModal}
        setOpen={() => setConfirmModal(false)}
        isLoading={isLoading}
      />
    </section>
  );
};
